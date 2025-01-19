import json
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

from backend.services.backend_api_client import BackendAPIClient


async def display_postgres_etl_section():
    load_dotenv()
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        username = st.text_input("Username", os.getenv("POSTGRES_USERNAME", "postgres"))
    with col2:
        password = st.text_input("Password", os.getenv("POSTGRES_PASSWORD", "postgres"), type="password")
    with col3:
        host = st.text_input("Host", os.getenv("POSTGRES_HOST", "localhost"))
    with col4:
        port = st.number_input("Port", os.getenv("POSTGRES_PORT", 5432))
    with col5:
        database = st.text_input("Database", os.getenv("POSTGRES_DATABASE", "postgres"))
    if st.button("Fetch data"):
        db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        try:
            engine = create_engine(
                db_url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                connect_args={"connect_timeout": 10}
            )
            with engine.connect() as connection:
                raw_connection = connection.connection
                checkpoint_data = {
                    "executors": pd.read_sql_query("SELECT * FROM \"Executors\"", raw_connection).to_dict('records'),
                    "orders": pd.read_sql_query("SELECT * FROM \"Order\"", raw_connection).to_dict('records'),
                    "trade_fill": pd.read_sql_query("SELECT * FROM \"TradeFill\"", raw_connection).to_dict('records'),
                    "controllers": pd.read_sql_query("SELECT * FROM \"Controllers\"", raw_connection).to_dict('records')
                }
            return checkpoint_data
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    else:
        st.stop()


def display_sqlite_etl_section(backend_api: BackendAPIClient):
    db_paths = backend_api.list_databases()
    dbs_dict = backend_api.read_databases(db_paths)
    healthy_dbs = [db["db_path"].replace("sqlite:///", "") for db in dbs_dict if db["healthy"]]
    with st.expander("ETL Tool"):
        st.markdown("""
        In this tool, you can easily fetch and combine different databases. Just follow these simple steps:
        - Choose the ones you want to analyze (only non-corrupt databases are available)
        - Merge them into a checkpoint
        - Start analyzing
        """)
        if len(healthy_dbs) == 0:
            st.warning(
                "Oops, it looks like there are no databases here. If you uploaded a file and it's not showing up, "
                "you can check the status report.")
            st.dataframe([db["status"] for db in dbs_dict], use_container_width=True)
        else:
            st.markdown("#### Select Databases to Merge")
            selected_dbs = st.multiselect("Choose the databases you want to merge", healthy_dbs,
                                          label_visibility="collapsed")
            if len(selected_dbs) == 0:
                st.warning("No databases selected. Please select at least one database.")
            else:
                st.markdown("#### Create Checkpoint")
                if st.button("Save"):
                    response = backend_api.create_checkpoint(selected_dbs)
                    if response["message"] == "Checkpoint created successfully.":
                        st.success("Checkpoint created successfully!")
                    else:
                        st.error("Error creating checkpoint. Please try again.")
    checkpoints_list = backend_api.list_checkpoints(full_path=True)
    if len(checkpoints_list) == 0:
        st.warning("No checkpoints detected. Please create a new one to continue.")
        st.stop()
    else:
        selected_checkpoint = st.selectbox("Select a checkpoint to load", checkpoints_list)
        checkpoint_data = fetch_checkpoint_data(backend_api, selected_checkpoint)
        checkpoint_data["executors"] = json.loads(checkpoint_data["executors"])
        checkpoint_data["orders"] = json.loads(checkpoint_data["orders"])
        checkpoint_data["trade_fill"] = json.loads(checkpoint_data["trade_fill"])
        checkpoint_data["controllers"] = json.loads(checkpoint_data["controllers"])
        return checkpoint_data


@st.cache_data
def fetch_checkpoint_data(_backend_api: BackendAPIClient, selected_checkpoint: str):
    checkpoint_data = _backend_api.load_checkpoint(selected_checkpoint)
    return checkpoint_data
