import json

import streamlit as st

from backend.services.backend_api_client import BackendAPIClient


def display_etl_section(backend_api: BackendAPIClient):
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
        checkpoint_data = fetch_checkpoint_data(selected_checkpoint)
        checkpoint_data["executors"] = json.loads(checkpoint_data["executors"])
        checkpoint_data["orders"] = json.loads(checkpoint_data["orders"])
        checkpoint_data["trade_fill"] = json.loads(checkpoint_data["trade_fill"])
        checkpoint_data["controllers"] = json.loads(checkpoint_data["controllers"])
        return checkpoint_data


@st.cache_data
def fetch_checkpoint_data(selected_checkpoint: str):
    backend_api = BackendAPIClient()
    checkpoint_data = backend_api.load_checkpoint(selected_checkpoint)
    return checkpoint_data
