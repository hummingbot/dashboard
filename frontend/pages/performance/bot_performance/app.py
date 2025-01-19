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
from frontend.visualization.performance_etl import display_postgres_etl_section, display_sqlite_etl_section


async def main():
    initialize_st_page(title="Bot Performance", icon="🚀", initial_sidebar_state="collapsed")
    st.session_state["default_config"] = {}
    backend_api = get_backend_api_client()

    st.subheader("🔫 DATA SOURCE")
    selected_db = st.selectbox("Select DB connector", ["PostgreSQL", "SQLite"])
    if selected_db == "SQLite":
        checkpoint_data = display_sqlite_etl_section(backend_api)
    else:
        checkpoint_data = await display_postgres_etl_section()
        if checkpoint_data is None:
            st.warning("Unable to retrieve data. Ensure the PostgreSQL database is accessible and contains relevant information.")
            st.stop()
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
