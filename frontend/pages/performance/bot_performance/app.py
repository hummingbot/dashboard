import asyncio

import streamlit as st

from backend.utils.performance_data_source import PerformanceDataSource
from frontend.st_utils import get_backend_api_client, initialize_st_page
from frontend.visualization.bot_performance import (
    display_execution_analysis,
    display_global_results,
    display_performance_summary_table,
    display_tables_section,
)
from frontend.visualization.performance_etl import display_etl_section


async def main():
    initialize_st_page(title="Bot Performance", icon="🚀", initial_sidebar_state="collapsed")
    st.session_state["default_config"] = {}
    backend_api = get_backend_api_client()

    st.subheader("🔫 DATA SOURCE")
    checkpoint_data = display_etl_section(backend_api)
    data_source = PerformanceDataSource(checkpoint_data)
    st.divider()

    st.subheader("📊 OVERVIEW")
    display_performance_summary_table(data_source.get_executors_df(), data_source.executors_with_orders)
    st.divider()

    st.subheader("🌎 GLOBAL RESULTS")
    display_global_results(data_source)
    st.divider()

    st.subheader("🧨 EXECUTION")
    display_execution_analysis(data_source)
    st.divider()

    st.subheader("💾 EXPORT")
    display_tables_section(data_source)


if __name__ == "__main__":
    asyncio.run(main())
