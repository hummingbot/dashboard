from streamlit_elements import mui, lazy
from ui_components.dashboard import Dashboard
import streamlit as st
import time
import pandas as pd
import datetime

from utils.backend_api_client import BackendAPIClient

TRADES_TO_SHOW = 5
WIDE_COL_WIDTH = 150
MEDIUM_COL_WIDTH = 140
backend_api_client = BackendAPIClient.get_instance()


def stop_bot(bot_name):
    backend_api_client.stop_bot(bot_name)
    backend_api_client.stop_container(bot_name)
    backend_api_client.remove_container(bot_name)


def archive_bot(bot_name):
    backend_api_client.stop_container(bot_name)
    backend_api_client.remove_container(bot_name)


class BotPerformanceCardV2(Dashboard.Item):
    def __init__(self, board, x, y, w, h, **item_props):
        super().__init__(board, x, y, w, h, **item_props)

    def __call__(self, bot_config: dict):
        bot_name = bot_config["bot_name"]
        status = bot_config.get("status", {"running_status": "not available"})
        is_running = status["running_status"] == "running"
        global_performance = status.get("global_performance")
        with mui.Card(key=self._key,
                      sx={"display": "flex", "flexDirection": "column", "borderRadius": 2, "overflow": "auto"},
                      elevation=2):
            color = "green" if is_running else "grey"
            mui.CardHeader(
                title=bot_name,
                subheader=status["running_status"],
                avatar=mui.Avatar("🤖", sx={"bgcolor": color}),
                action=mui.IconButton(mui.icon.Stop, onClick=lambda: stop_bot(bot_name)) if is_running else mui.IconButton(mui.icon.Archive, onClick=lambda: archive_bot(bot_name)),
                className=self._draggable_class)
            if is_running:
                with mui.CardContent(sx={"flex": 1}):
                    # Balances Table
                    mui.Typography("Balances", variant="h6")

                    balances = status.get("total_balances", {})
                    if balances:
                        rows = [(exchange, symbol, round(float(value), 2)) for exchange, inner_dict in balances.items() for symbol, value
                                in inner_dict.items()]
                        df_balances = pd.DataFrame(rows, columns=["Exchange", "Currency", "Amount"]).reset_index().rename(columns={"index": "id"})

                        balances_rows = df_balances.to_dict(orient='records')
                        balances_cols = [{'field': col, 'headerName': col} for col in df_balances.columns]

                        for column in balances_cols:
                            # Customize width for 'exchange' column
                            if column['field'] == 'Exchange':
                                column['width'] = WIDE_COL_WIDTH
                        mui.DataGrid(
                            rows=balances_rows,
                            columns=balances_cols,
                            autoHeight=True,
                            density="compact",
                            disableColumnSelector=True,
                            hideFooter=True,
                            initialState={"columns": {"columnVisibilityModel": {"id": False}}})
                    else:
                        mui.Typography(str(balances), sx={"fontSize": "0.75rem"})
                    mui.Divider(sx={"margin": "1rem 0"})
                    # Controllers Table
                    mui.Typography("Controllers", variant="h6", sx={"marginTop": 2})
                    controllers = status.get("controllers")
                    if controllers:
                        controllers_list = []
                        for controller, inner_dict in controllers.items():
                            controllers_list.append({
                                "Controller ID": controller,
                                "Realized PNL ($)": inner_dict.get("realized_pnl_quote", 0),
                                "Unrealized PNL ($)": inner_dict.get("unrealized_pnl_quote", 0),
                                "GLOBAL PNL ($)": inner_dict.get("global_pnl_quote", 0),
                                # "global_pnl_pct": inner_dict.get("global_pnl_pct", 0),
                                "Volume ($)": inner_dict.get("total_volume_traded", 0),
                            })

                        df_controllers = pd.DataFrame(controllers_list).reset_index().rename(columns={"index": "id"})
                        controllers_rows = df_controllers.to_dict(orient='records')
                        controllers_cols = [{'field': col, 'headerName': col} for col in df_controllers.columns]
                        for column in controllers_cols:
                            # Customize width for 'exchange' column
                            column['width'] = WIDE_COL_WIDTH
                        mui.DataGrid(
                            rows=controllers_rows,
                            columns=controllers_cols,
                            autoHeight=True,
                            density="compact",
                            disableColumnSelector=True,
                            hideFooter=True,
                            initialState={"columns": {"columnVisibilityModel": {"id": False}}})
                    else:
                        mui.Typography(str(controllers), sx={"fontSize": "0.75rem"})
                    mui.Divider(sx={"margin": "1rem 0"})
                    mui.Typography("Global Performance", variant="h6")
                    if global_performance:
                        global_pnl_quote = global_performance.get("global_pnl_quote", 0)
                        global_pnl_pct = global_performance.get("global_pnl_pct", 0)
                        total_volume_traded = global_performance.get("total_volume_traded", 0)
                        mui.Typography(f"       Global PnL (Quote): {global_pnl_quote} | Global PnL %: {global_pnl_pct} | Total Volume Traded: {total_volume_traded}")
                    else:
                        mui.Typography("No global performance data available", sx={"fontSize": "0.75rem"})
