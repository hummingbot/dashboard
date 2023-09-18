from streamlit_elements import mui, lazy

import constants
from utils.file_templates import directional_trading_controller_template
from utils.os_utils import save_file
from .dashboard import Dashboard


class DirectionalStrategyCreationCard(Dashboard.Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._strategy_name = "CustomStrategy"
        self._strategy_type = "directional"

    def _set_strategy_name(self, event):
        self._strategy_name = event.target.value

    def _set_strategy_type(self, _, childs):
        self._strategy_type = childs.props.value

    def _create_strategy(self):
        if self._strategy_type == "directional":
            strategy_code = directional_trading_controller_template(self._strategy_name)
        save_file(name=f"{self._strategy_name.lower()}.py", content=strategy_code,
                  path=constants.CONTROLLERS_PATH)

    def __call__(self):
        with mui.Paper(key=self._key, sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"}, elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.icon.NoteAdd()
                mui.Typography("Create new strategy", variant="h6")

            with mui.Grid(container=True, spacing=2, sx={"padding": "10px"}):
                with mui.Grid(item=True, xs=5):
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.FormHelperText("Template name")
                        with mui.Select(label="Select strategy type", defaultValue="directional",
                                        variant="standard", onChange=lazy(self._set_strategy_type)):
                            mui.MenuItem("Directional", value="directional")
                with mui.Grid(item=True, xs=5):
                    with mui.FormControl(variant="standard", sx={"width": "100%"}):
                        mui.TextField(defaultValue="CustomStrategy", label="Strategy Name",
                                      variant="standard", onChange=lazy(self._set_strategy_name))
                with mui.Grid(item=True, xs=2):
                    with mui.Button(variant="contained", onClick=self._create_strategy):
                        mui.icon.Add()
                        mui.Typography("Create", variant="body1")
