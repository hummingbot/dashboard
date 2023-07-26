from streamlit_elements import mui
from ui_components.dashboard import Dashboard


class BotPerformanceCard(Dashboard.Item):
    DEFAULT_CONTENT = (
        "This impressive paella is a perfect party dish and a fun meal to cook "
        "together with your guests. Add 1 cup of frozen peas along with the mussels, "
        "if you like."
    )

    def __init__(self, board, x, y, w, h, **item_props):
        super().__init__(board, x, y, w, h, isResizable=False, **item_props)

    def __call__(self, bot_config: dict):
        with mui.Card(key=self._key,
                      sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"},
                      elevation=2):
            color = "green" if bot_config["is_running"] else "red"
            start_date = bot_config.get("start_date", "Not Available")
            mui.CardHeader(
                title=bot_config["bot_name"],
                subheader=f"Running since {start_date}",
                avatar=mui.Avatar("🤖", sx={"bgcolor": color}),
                className=self._draggable_class,
            )

            with mui.CardContent(sx={"flex": 1}):
                mui.Typography("Status:")
                mui.Typography(bot_config["status"])
                mui.Typography("Trades:")
                mui.Typography(str(bot_config["trades"]))

            with mui.CardActions(disableSpacing=True):
                mui.IconButton(mui.icon.Stop)
                mui.IconButton(mui.icon.Share)
