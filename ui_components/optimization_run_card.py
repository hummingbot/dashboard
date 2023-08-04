import threading

import optuna
from streamlit_elements import mui, lazy

import constants
from utils.os_utils import get_python_files_from_directory, \
    get_function_from_file
from .dashboard import Dashboard


class OptimizationRunCard(Dashboard.Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._optimization_name = None
        self._number_of_trials = 2000

    def _set_optimization_name(self, _, childs):
        self._optimization_name = childs.props.value

    def _set_number_of_trials(self, event):
        self._number_of_trials = int(event.target.value)

    def _run_optimization(self):
        study_name = self._optimization_name.split('/')[-1].split('.')[0]
        study = optuna.create_study(direction="maximize", study_name=study_name,
                                    storage="sqlite:///data/backtesting/backtesting_report.db",
                                    load_if_exists=True)
        objective = get_function_from_file(file_path=self._optimization_name,
                                           function_name="objective")

        def optimization_process():
            study.optimize(objective, n_trials=self._number_of_trials)

        optimization_thread = threading.Thread(target=optimization_process)
        optimization_thread.start()

    def __call__(self):
        optimizations = get_python_files_from_directory(constants.OPTIMIZATIONS_PATH)
        with mui.Paper(key=self._key, sx={"display": "flex", "flexDirection": "column", "borderRadius": 3, "overflow": "hidden"}, elevation=1):
            with self.title_bar(padding="10px 15px 10px 15px", dark_switcher=False):
                mui.icon.AutoFixHigh()
                mui.Typography("Run a optimization", variant="h6")

            if len(optimizations) == 0:
                mui.Alert("No optimizations available, please create one.", severity="warning", sx={"width": "100%"})
                return
            else:
                if self._optimization_name is None:
                    self._optimization_name = optimizations[0]
                with mui.Grid(container=True, spacing=2, sx={"padding": "10px"}):
                    with mui.Grid(item=True, xs=4):
                        with mui.FormControl(variant="standard", sx={"width": "100%"}):
                            mui.FormHelperText("Study name")
                            with mui.Select(defaultValue=optimizations[0],
                                            variant="standard", onChange=lazy(self._set_optimization_name)):
                                for optimization in optimizations:
                                    mui.MenuItem(f"{optimization.split('/')[-1].split('.')[0]}", value=optimization)
                    with mui.Grid(item=True, xs=4):
                        with mui.FormControl(variant="standard", sx={"width": "100%"}):
                            mui.TextField(defaultValue=self._optimization_name, label="Number of trials", type="number",
                                      variant="standard", onChange=lazy(self._set_number_of_trials))
                    with mui.Grid(item=True, xs=4):
                        with mui.Button(variant="contained", onClick=self._run_optimization, sx={"width": "100%"}):
                            mui.icon.PlayCircleFilled()
                            mui.Typography("Run", variant="button")
