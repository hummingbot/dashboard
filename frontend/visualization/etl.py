import os
import json
import streamlit as st

from backend.services.backend_api_client import BackendAPIClient


def display_etl_section(backend_api: BackendAPIClient):
    """
    - Display the ETL section of the page. If there are no databases available, the user can upload a new one.
    - If there are databases available, the user can select which ones to merge.
    - The user can also clean the tables before loading new data.
    - The function returns an ETLPerformance object with the merged database. If there is no persisted database, the
    function stops the execution.
    """
    dbs = backend_api.read_databases()
    healthy_dbs = [db["db_name"] for db in dbs if db["healthy"]]

    st.subheader("🔫 Data source")
    with st.expander("ETL Tool"):
        st.markdown("""
        In this tool, you can easily fetch and combine different databases. Just follow these simple steps:

        - Choose the ones you want to analyze (only healthy databases are available)
        - Merge them together
        """)
        if len(healthy_dbs) == 0:
            st.warning(
                "Oops, it looks like there are no databases here. If you uploaded a file and it's not showing up, you can check the status report.")
            st.dataframe([db["status"] for db in dbs], use_container_width=True)
        else:
            st.markdown("#### Select Databases to Merge")
            selected_dbs = st.multiselect("Choose the databases you want to merge", healthy_dbs, label_visibility="collapsed")
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
        checkpoint_data = backend_api.load_checkpoint(selected_checkpoint)
        checkpoint_data["executor"] = json.loads(checkpoint_data["executor"])
        checkpoint_data["order"] = json.loads(checkpoint_data["order"])
        checkpoint_data["trade_fill"] = json.loads(checkpoint_data["trade_fill"])
        return checkpoint_data

# TODO: Add upload section
# def load_database(uploaded_db, root_path: str = "data/uploaded"):
#     file_contents = uploaded_db.read()
#     with open(os.path.join(root_path, uploaded_db.name), "wb") as f:
#         f.write(file_contents)
#     st.success("File uploaded and saved successfully!")
