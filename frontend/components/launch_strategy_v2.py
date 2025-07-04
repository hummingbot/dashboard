import time
import re

import streamlit as st
from streamlit_elements import lazy, mui

from ..st_utils import get_backend_api_client
from .dashboard import Dashboard


class LaunchStrategyV2(Dashboard.Item):
    DEFAULT_ROWS = []
    DEFAULT_COLUMNS = [
        {"field": 'config_base', "headerName": 'Config Base', "minWidth": 250, "editable": False, },
        {"field": 'version', "headerName": 'Version', "width": 100, "editable": False, },
        {"field": 'controller_name', "headerName": 'Controller Name', "width": 180, "editable": False, },
        {"field": 'controller_type', "headerName": 'Controller Type', "width": 150, "editable": False, },
        {"field": 'connector_name', "headerName": 'Connector', "width": 130, "editable": False, },
        {"field": 'trading_pair', "headerName": 'Trading Pair', "width": 130, "editable": False, },
        {"field": 'total_amount_quote', "headerName": 'Amount (USDT)', "width": 120, "editable": False, },
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._backend_api_client = get_backend_api_client()
        self._controller_configs_available = self._get_controller_configs()
        self._controller_config_selected = None
        self._bot_name = None
        self._image_name = "hummingbot/hummingbot:latest"
        self._credentials = "master_account"
        self._max_global_drawdown_quote = None
        self._max_controller_drawdown_quote = None

    def _set_bot_name(self, event):
        self._bot_name = event.target.value

    def _set_image_name(self, _, childs):
        self._image_name = childs.props.value

    def _set_credentials(self, _, childs):
        self._credentials = childs.props.value

    def _set_controller(self, event):
        self._controller_selected = event.target.value

    def _handle_row_selection(self, params, _):
        self._controller_config_selected = [param + ".yml" for param in params]

    def _set_max_global_drawdown_quote(self, event):
        try:
            self._max_global_drawdown_quote = float(event.target.value) if event.target.value else None
        except ValueError:
            self._max_global_drawdown_quote = None

    def _set_max_controller_drawdown_quote(self, event):
        try:
            self._max_controller_drawdown_quote = float(event.target.value) if event.target.value else None
        except ValueError:
            self._max_controller_drawdown_quote = None
    
    def _get_controller_configs(self):
        """Get all controller configurations using the new API."""
        try:
            return self._backend_api_client.controllers.list_controller_configs()
        except Exception as e:
            st.error(f"Failed to fetch controller configs: {e}")
            return []
    
    @staticmethod
    def _filter_hummingbot_images(images):
        """Filter images to only show Hummingbot-related ones."""
        hummingbot_images = []
        pattern = r'.+/hummingbot:'
        
        for image in images:
            try:
                if re.match(pattern, image):
                    hummingbot_images.append(image)
            except Exception:
                continue
        
        return hummingbot_images

    def launch_new_bot(self, *args, **kwargs):
        print(f"DEBUG: launch_new_bot called with args={args}, kwargs={kwargs}")
        st.write("DEBUG: Launch button was clicked!")
        
        if not self._bot_name:
            st.warning("You need to define the bot name.")
            return
        if not self._image_name:
            st.warning("You need to select the hummingbot image.")
            return
        if not self._controller_config_selected or len(self._controller_config_selected) == 0:
            st.warning("You need to select the controllers configs. Please select at least one controller "
                       "config by clicking on the checkbox.")
            return
        start_time_str = time.strftime("%Y%m%d-%H%M")
        bot_name = f"{self._bot_name}-{start_time_str}"
        try:
            # Use the new deploy_v2_controllers method
            deploy_config = {
                "instance_name": bot_name,
                "credentials_profile": self._credentials,
                "controllers_config": [config.replace(".yml", "") for config in self._controller_config_selected],
                "image": self._image_name,
            }
            
            # Add optional drawdown parameters if set
            if self._max_global_drawdown_quote is not None:
                deploy_config["max_global_drawdown_quote"] = self._max_global_drawdown_quote
            if self._max_controller_drawdown_quote is not None:
                deploy_config["max_controller_drawdown_quote"] = self._max_controller_drawdown_quote
            
            self._backend_api_client.bot_orchestration.deploy_v2_controllers(**deploy_config)
        except Exception as e:
            st.error(f"Failed to deploy bot: {e}")
            return
        with st.spinner('Starting Bot... This process may take a few seconds'):
            time.sleep(3)

    def delete_selected_configs(self, *args, **kwargs):
        print(f"DEBUG: delete_selected_configs called with args={args}, kwargs={kwargs}")
        st.write("DEBUG: Delete button was clicked!")
        
        if self._controller_config_selected:
            try:
                for config in self._controller_config_selected:
                    # Remove .yml extension if present
                    config_name = config.replace(".yml", "")
                    response = self._backend_api_client.controllers.delete_controller_config(config_name)
                    st.success(f"Deleted {config_name}: {response}")
                self._controller_configs_available = self._get_controller_configs()
            except Exception as e:
                st.error(f"Failed to delete configs: {e}")
        else:
            st.warning("You need to select the controllers configs that you want to delete.")

    def __call__(self):
        with mui.Box(key=self._key,
                     sx={"display": "flex", "flexDirection": "column", "width": "100%", "padding": "24px"}):
            # Page Header
            mui.Typography("🚀 Deploy Trading Bot", variant="h4", sx={"marginBottom": "8px", "fontWeight": "700"})
            mui.Typography("Configure and deploy your automated trading strategy", variant="subtitle1", sx={"color": "text.secondary", "marginBottom": "32px"})
            
            with mui.Box():
                # Bot Configuration Section
                mui.Typography("🤖 Bot Configuration", variant="h6", sx={"marginBottom": "20px", "fontWeight": "600"})
                
                with mui.Grid(container=True, spacing=3):
                    # Instance Name
                    with mui.Grid(item=True, xs=4):
                        mui.TextField(
                            label="Instance Name", 
                            variant="outlined", 
                            onChange=lazy(self._set_bot_name),
                            placeholder="Enter a unique name for your bot instance",
                            sx={"width": "100%"}
                        )
                    
                    # Credentials Selection
                    with mui.Grid(item=True, xs=4):
                        try:
                            available_credentials = self._backend_api_client.accounts.list_accounts()
                            with mui.FormControl(variant="outlined", sx={"width": "100%"}):
                                mui.InputLabel("Credentials Profile")
                                with mui.Select(
                                    label="Credentials Profile", 
                                    defaultValue="master_account",
                                    variant="outlined", 
                                    onChange=lazy(self._set_credentials),
                                    sx={"width": "100%"}
                                ):
                                    for master_config in available_credentials:
                                        mui.MenuItem(master_config, value=master_config)
                        except Exception as e:
                            st.error(f"Failed to fetch credentials: {e}")
                    
                    # Docker Image Selection
                    with mui.Grid(item=True, xs=4):
                        try:
                            all_images = self._backend_api_client.docker.get_available_images("hummingbot")
                            available_images = self._filter_hummingbot_images(all_images)
                            
                            if not available_images:
                                # Fallback to default if no hummingbot images found
                                available_images = ["hummingbot/hummingbot:latest"]
                            
                            # Ensure default image is in the list
                            default_image = "hummingbot/hummingbot:latest"
                            if default_image not in available_images:
                                available_images.insert(0, default_image)
                            
                            with mui.FormControl(variant="outlined", sx={"width": "100%"}):
                                mui.InputLabel("Hummingbot Image")
                                with mui.Select(
                                    label="Hummingbot Image", 
                                    defaultValue=default_image,
                                    variant="outlined", 
                                    onChange=lazy(self._set_image_name),
                                    sx={"width": "100%"}
                                ):
                                    for image in available_images:
                                        mui.MenuItem(image, value=image)
                        except Exception as e:
                            st.error(f"Failed to fetch available images: {e}")
                
                # Risk Management Section
                mui.Divider(sx={"margin": "24px 0 20px 0"})
                mui.Typography("⚠️ Risk Management", variant="h6", sx={"marginBottom": "16px", "fontWeight": "600"})
                mui.Typography("Set maximum drawdown limits in USDT to protect your capital", variant="body2", sx={"marginBottom": "16px", "color": "text.secondary"})
                
                with mui.Grid(container=True, spacing=3):
                    with mui.Grid(item=True, xs=6):
                        mui.TextField(
                            label="Max Global Drawdown (USDT)", 
                            variant="outlined", 
                            type="number",
                            placeholder="e.g., 1000",
                            onChange=lazy(self._set_max_global_drawdown_quote), 
                            sx={"width": "100%"},
                            InputProps={"startAdornment": mui.InputAdornment("$", position="start")}
                        )
                    with mui.Grid(item=True, xs=6):
                        mui.TextField(
                            label="Max Controller Drawdown (USDT)", 
                            variant="outlined", 
                            type="number",
                            placeholder="e.g., 500",
                            onChange=lazy(self._set_max_controller_drawdown_quote), 
                            sx={"width": "100%"},
                            InputProps={"startAdornment": mui.InputAdornment("$", position="start")}
                        )
                
                # Controllers Section Header
                mui.Divider(sx={"margin": "24px 0 20px 0"})
                mui.Typography("🎛️ Controller Selection", variant="h6", sx={"marginBottom": "8px", "fontWeight": "600"})
                mui.Typography("Select the trading controllers you want to deploy with this bot instance", variant="body2", sx={"marginBottom": "16px", "color": "text.secondary"})
                all_controllers_config = self._controller_configs_available
                data = []
                for config in all_controllers_config:
                    # Handle case where config might be a string instead of dict
                    if isinstance(config, str):
                        st.warning(f"Unexpected config format: {config}. Expected a dictionary.")
                        continue
                    
                    # Handle both old and new config format
                    config_name = config.get("config_name", config.get("id", "Unknown"))
                    config_data = config.get("config", config)  # New format has config nested
                    
                    connector_name = config_data.get("connector_name", "Unknown")
                    trading_pair = config_data.get("trading_pair", "Unknown")
                    total_amount_quote = float(config_data.get("total_amount_quote", 0))
                    stop_loss = float(config_data.get("stop_loss", 0))
                    take_profit = float(config_data.get("take_profit", 0))
                    trailing_stop = config_data.get("trailing_stop", {"activation_price": 0, "trailing_delta": 0})
                    time_limit = float(config_data.get("time_limit", 0))
                    
                    # Extract controller info
                    controller_name = config_data.get("controller_name", config_name)
                    controller_type = config_data.get("controller_type", "generic")
                    
                    # Fix config base and version splitting - version should be the last part after underscore
                    config_parts = config_name.split("_")
                    if len(config_parts) > 1:
                        # Version is the last part, config_base is everything before that
                        version = config_parts[-1]
                        config_base = "_".join(config_parts[:-1])
                    else:
                        config_base = config_name
                        version = "NaN"
                    
                    data.append({
                        "id": config_name, "config_base": config_base, "version": version,
                        "controller_name": controller_name,
                        "controller_type": controller_type,
                        "connector_name": connector_name, "trading_pair": trading_pair,
                        "total_amount_quote": total_amount_quote})

                # Controller Selection Table
                with mui.Paper(
                    sx={
                        "marginTop": "16px",
                        "borderRadius": "12px",
                        "overflow": "hidden",
                        "boxShadow": "0 4px 20px rgba(0,0,0,0.1)"
                    },
                    elevation=0
                ):
                    # Table Header
                    with mui.Box(sx={"padding": "20px 24px 16px 24px", "backgroundColor": "rgba(25, 118, 210, 0.04)", "borderBottom": "1px solid rgba(0,0,0,0.12)"}):
                        with mui.Grid(container=True, spacing=2, alignItems="center"):
                            with mui.Grid(item=True, xs=8):
                                mui.Typography("Available Controller Configurations", variant="h6", sx={"fontWeight": "600"})
                                mui.Typography(f"{len(data)} configurations available", variant="body2", sx={"color": "text.secondary", "marginTop": "4px"})
                            with mui.Grid(item=True, xs=2):
                                mui.Button(
                                    "Delete Selected",
                                    onClick=lazy(self.delete_selected_configs),
                                    variant="outlined",
                                    color="error",
                                    startIcon=mui.icon.Delete(),
                                    sx={
                                        "width": "100%", 
                                        "borderRadius": "8px",
                                        "textTransform": "none",
                                        "fontWeight": "500"
                                    }
                                )
                            with mui.Grid(item=True, xs=2):
                                mui.Button(
                                    "Deploy Bot",
                                    onClick=lazy(self.launch_new_bot),
                                    variant="contained",
                                    color="primary",
                                    startIcon=mui.icon.RocketLaunch(),
                                    sx={
                                        "width": "100%",
                                        "borderRadius": "8px", 
                                        "textTransform": "none",
                                        "fontWeight": "600",
                                        "boxShadow": "0 4px 12px rgba(25, 118, 210, 0.3)"
                                    }
                                )
                    
                    # Data Grid
                    with mui.Box(sx={"height": "600px", "width": "100%"}):
                        mui.DataGrid(
                            columns=self.DEFAULT_COLUMNS,
                            rows=data,
                            pageSize=15,
                            rowsPerPageOptions=[15, 25, 50],
                            checkboxSelection=True,
                            disableSelectionOnClick=True,
                            disableColumnResize=False,
                            onSelectionModelChange=self._handle_row_selection,
                            sx={
                                "border": "none",
                                "& .MuiDataGrid-cell": {
                                    "borderBottom": "1px solid rgba(0,0,0,0.08)"
                                },
                                "& .MuiDataGrid-columnHeaders": {
                                    "backgroundColor": "rgba(0,0,0,0.02)",
                                    "borderBottom": "2px solid rgba(0,0,0,0.12)",
                                    "fontWeight": "600"
                                },
                                "& .MuiDataGrid-row:hover": {
                                    "backgroundColor": "rgba(25, 118, 210, 0.04)"
                                }
                            }
                        )
