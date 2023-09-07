from streamlit_elements import mui, lazy
import datetime

import constants
from utils.file_templates import strategy_optimization_template
from utils.os_utils import save_file, load_controllers
from .dashboard import Dashboard


class OptimizationCreationCard(Dashboard.Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = datetime.datetime.now()
        self._optimization_version = f"{today.day:02d}-{today.month:02d}-{today.year}"
        self._optimization_name = None
        self._strategy_name = None

    def _set_optimization_version(self, event):
        self._optimization_version = event.target.value

    def _set_strategy_name(self, _, childs):
        self._strategy_name = childs.props.value

    def _create_optimization(self, strategy_info):
        strategy_code = strategy_optimization_template(strategy_info)
        save_file(name=f"{self._strategy_name.lower()}_v_{self._optimization_version}.py", content=strategy_code,
                  path=constants.OPTIMIZATIONS_PATH)

    def __call__(self):
        available_strategies = load_controllers(constants.DIRECTIONAL_STRATEGIES_PATH)
        strategy_names = list(available_strategies.keys())
        with mui.Paper(key=self._key,
                       sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"},
                       elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.icon.NoteAdd()
                mui.Typography("Create study", variant="h6")
            if len(strategy_names) == 0:
                mui.Alert("No strategies available, please create one to optimize it", severity="warning",
                          sx={"width": "100%"})
                return
            else:
                if self._strategy_name is None:
                    self._strategy_name = strategy_names[0]
                with mui.Grid(container=True, spacing=2, sx={"padding": "10px"}):
                    with mui.Grid(item=True, xs=4):
                        with mui.FormControl(variant="standard", sx={"width": "100%"}):
                            mui.FormHelperText("Strategy name")
                            with mui.Select(label="Select strategy", defaultValue=strategy_names[0],
                                            variant="standard", onChange=lazy(self._set_strategy_name)):
                                for strategy in strategy_names:
                                    mui.MenuItem(strategy, value=strategy)
                    with mui.Grid(item=True, xs=4):
                        with mui.FormControl(variant="standard", sx={"width": "100%"}):
                            mui.TextField(defaultValue=self._optimization_version, label="Optimization version",
                                          variant="standard", onChange=lazy(self._set_optimization_version))
                    with mui.Grid(item=True, xs=4):
                        with mui.Button(variant="contained", onClick=lambda x: self._create_optimization(
                                available_strategies[self._strategy_name]), sx={"width": "100%"}):
                            mui.icon.Add()
                            mui.Typography("Create", variant="body1")
