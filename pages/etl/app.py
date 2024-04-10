import streamlit as st
import os
import pandas as pd
import logging
from psycopg2 import OperationalError

from utils.postgres_connector import PostgresConnector
from utils.database_orchestrator import DatabaseOrchestrator
from utils.s3_utils import S3Manager
from utils.st_utils import initialize_st_page
from utils.sqlite_manager import SQLiteManager
from dotenv import load_dotenv

load_dotenv()

initialize_st_page("ETL Page", layout="wide", icon="📦")


st.subheader("🔼 Upload SQLite locally")
uploaded_db = st.file_uploader("Select a Hummingbot SQLite Database", type=["sqlite", "db"])
if uploaded_db is not None:
    file_contents = uploaded_db.read()
    with open(os.path.join("data/uploaded", uploaded_db.name), "wb") as f:
        f.write(file_contents)
    st.success("File uploaded and saved successfully!")
    selected_db = SQLiteManager(uploaded_db.name)

st.divider()

st.subheader("🔽 Extract from S3")
col1, col2, col3, col4 = st.columns(4)
with col1:
    bucket_name = st.text_input("Bucket name", os.environ.get("S3_BUCKET_NAME"))
with col2:
    access_key_id = st.text_input("Access Key ID", os.environ.get("S3_ACCESS_KEY"), type="password")
with col3:
    secret_access_key = st.text_input("Secret Access Key", os.environ.get("S3_SECRET_KEY"), type="password")
with col4:
    region_name = st.text_input("Region Name", "ap-northeast-1")

if all([bucket_name, access_key_id, secret_access_key, region_name]):
    fetch_all = st.checkbox("Fetch all databases", True)
    replace = st.checkbox("Replace existing databases", False)
    s3_manager = S3Manager(bucket_name=bucket_name,
                           access_key_id=access_key_id,
                           secret_access_key=secret_access_key,
                           region_name=region_name)
    dbs = s3_manager.list_all_sqlite_files()

    if not fetch_all:
        df = pd.DataFrame({'SQLite File': dbs})
        df['Select'] = False
        selected_indices = st.data_editor(df, hide_index=True, use_container_width=True)
        dbs = list(selected_indices[selected_indices["Select"]]["SQLite File"])
    if st.button("Fetch databases"):
        n_files = len(dbs)
        file_counter = 0
        with st.spinner("Fetching databases... Please don't close this page"):
            with st.expander("Check status"):
                st.write(f"{n_files} databases were founded. Starting download...")
                for db in dbs:
                    file_counter += 1
                    st.info(s3_manager.download_file(db, replace))
                    st.write(f"{(100 * file_counter / n_files):.2f} % Completed")
else:
    st.warning("Please fill in all the required fields to fetch databases from S3.")

st.divider()

st.subheader("🔄 Load into Postgres")
st.markdown("#### Database Connection")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    host = st.text_input("Host", "dashboard-db-1")
with col2:
    port = st.number_input("Port", value=5432, step=1)
with col3:
    db_name = st.text_input("DB Name", os.environ.get("POSTGRES_DB"))
with col4:
    db_user = st.text_input("DB User", os.environ.get("POSTGRES_USER"))
with col5:
    db_password = st.text_input("DB Password", os.environ.get("POSTGRES_PASSWORD"), type="password")
try:
    postgres_etl = PostgresConnector(host=host, port=port, database=db_name, user=db_user, password=db_password)
    st.success("Connected to PostgreSQL database successfully!")
except OperationalError as e:
    # Log the error message to Streamlit interface
    st.error(f"Error connecting to PostgreSQL database: {e}")
    # Log the error to the console or log file
    logging.error(f"Error connecting to PostgreSQL database: {e}")
    st.stop()

st.markdown("#### Select databases")
db_orchestrator = DatabaseOrchestrator()
healthy_dbs = [db.db_path for db in db_orchestrator.healthy_dbs]
with st.expander("Database status report"):
    st.dataframe(db_orchestrator.status_report, use_container_width=True)
selected_dbs = st.multiselect("SQLite databases", healthy_dbs)
if len(selected_dbs) == 0:
    st.warning("No databases selected. Please select at least one database.")
    st.stop()

st.markdown("#### Load databases")
clean_tables_before = st.checkbox("Clean tables before loading", False)
if st.button("Load into Postgres database"):
    tables_dict = db_orchestrator.get_tables(selected_dbs)
    postgres_etl.create_tables()
    if clean_tables_before:
        postgres_etl.clean_tables()
    postgres_etl.insert_data(tables_dict)
    st.success("Data loaded successfully!")
