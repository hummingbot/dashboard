from streamlit_elements import mui, lazy

import constants
from utils.file_templates import directional_strategy_template
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
            strategy_code = directional_strategy_template(self._strategy_name)
        save_file(name=f"{self._strategy_name.lower()}.py", content=strategy_code,
                  path=constants.DIRECTIONAL_STRATEGIES_PATH)

    def __call__(self):
        with mui.Paper(key=self._key, sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"}, elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.icon.NoteAdd()
                mui.Typography("Create new strategy", variant="h6")

            with mui.Stack(direction="row", spacing=2, justifyContent="space-evenly", alignItems="center", sx={"padding": "10px"}):
                with mui.Select(label="Select strategy type", defaultValue="directional",
                                variant="standard", onChange=lazy(self._set_strategy_type)):
                    mui.MenuItem("Directional", value="directional")
                mui.TextField(defaultValue="CustomStrategy", label="Strategy Name",
                              variant="standard", onChange=lazy(self._set_strategy_name))
                mui.IconButton(mui.icon.AddCircle, onClick=self._create_strategy, sx={"color": "primary.main"})
