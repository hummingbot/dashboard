import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utils.data_manipulation import StrategyData


class OptunaDBManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.db_path = f'sqlite:///{os.path.join("data/backtesting", db_name)}'
        self.engine = create_engine(self.db_path, connect_args={'check_same_thread': False})
        self.session_maker = sessionmaker(bind=self.engine)

    @property
    def tables(self):
        return self._get_tables()

    def _get_tables(self):
        try:
            with self.session_maker() as session:
                query = "SELECT name FROM sqlite_master WHERE type='table';"
                tables = pd.read_sql_query(query, session.connection())
            return tables["name"].tolist()
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def trials(self):
        return self._get_trials_table()

    def _get_trials_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM trials", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def studies(self):
        return self._get_studies_table()

    def _get_studies_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM studies", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def trial_params(self):
        return self._get_trial_params_table()

    def _get_trial_params_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM trial_params", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def trial_values(self):
        return self._get_trial_values_table()

    def _get_trial_values_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM trial_values", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def trial_system_attributes(self):
        return self._get_trial_system_attributes_table()

    def _get_trial_system_attributes_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM trial_system_attributes", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def trial_system_attributes(self):
        return self._get_trial_system_attributes_table()

    def _get_trial_system_attributes_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM trial_system_attributes", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def version_info(self):
        return self._get_version_info_table()

    def _get_version_info_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM version_info", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def study_directions(self):
        return self._get_study_directions_table()

    def _get_study_directions_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM study_directions", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def study_user_attributes(self):
        return self._get_study_user_attributes_table()

    def _get_study_user_attributes_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM study_user_attributes", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def study_system_attributes(self):
        return self._get_study_system_attributes_table()

    def _get_study_system_attributes_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM study_system_attributes", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def trial_user_attributes(self):
        return self._get_trial_user_attributes_table()

    def _get_trial_user_attributes_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM trial_user_attributes", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def trial_intermediate_values(self):
        return self._get_trial_intermediate_values_table()

    def _get_trial_intermediate_values_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM trial_intermediate_values", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def trial_heartbeats(self):
        return self._get_trial_heartbeats_table()

    def _get_trial_heartbeats_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM trial_heartbeats", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def alembic_version(self):
        return self._get_alembic_version_table()

    def _get_alembic_version_table(self):
        try:
            with self.session_maker() as session:
                df = pd.read_sql_query("SELECT * FROM alembic_version", session.connection())
            return df
        except Exception as e:
            return f"Error: {str(e)}"

    @property
    def merged_df(self):
        return self._get_merged_df()

    @staticmethod
    def _add_hovertext(x):
        summary_label = (f"<b>Trial ID: {x['trial_id']}</b><br>"
                         f"<b>Study: {x['study_name']}</b><br>"
                         f"--------------------<br>"
                         f"Accuracy: {100 * x['accuracy']:.2f} %<br>"
                         f"Avg Trading Time in Hours: {x['avg_trading_time_in_hours']:.2f}<br>"
                         f"Duration in Hours: {x['duration_in_hours']:.2f}<br>"
                         f"Loss Signals: {x['loss_signals']}<br>"
                         f"Max Drawdown [%]: {100 * x['max_drawdown_pct']:.2f} %<br>"
                         f"Max Drawdown [USD]: $ {x['max_drawdown_usd']:.2f}<br>"
                         f"Net Profit [%]: {100 * x['net_profit_pct']:.2f} %<br>"
                         f"Net Profit [$]: $ {x['net_profit_usd']:.2f}<br>"
                         f"Profit Factor: {x['profit_factor']:.2f}<br>"
                         f"Sharpe Ratio: {x['sharpe_ratio']:.4f}<br>"
                         f"Total Positions: {x['total_positions']}<br>"
                         f"Win Signals: {x['win_signals']}<br>"
                         f"Trial value: {x['value']}<br>"
                         f"Direction: {x['direction']}<br>"
                         )
        return summary_label

    def _get_merged_df(self):
        float_cols = ["accuracy", "avg_trading_time_in_hours", "duration_in_hours", "max_drawdown_pct", "max_drawdown_usd",
                      "net_profit_pct", "net_profit_usd", "profit_factor", "sharpe_ratio", "value"]
        int_cols = ["loss_signals", "total_positions", "win_signals"]
        merged_df = self.trials\
            .merge(self.studies, on="study_id")\
            .merge(pd.pivot(self.trial_user_attributes, index="trial_id", columns="key", values="value_json"),
                   on="trial_id")\
            .merge(self.trial_values, on="trial_id")\
            .merge(self.study_directions, on="study_id")
        merged_df[float_cols] = merged_df[float_cols].astype("float")
        merged_df[int_cols] = merged_df[int_cols].astype("int64")
        merged_df["hover_text"] = merged_df.apply(self._add_hovertext, axis=1)
        return merged_df

