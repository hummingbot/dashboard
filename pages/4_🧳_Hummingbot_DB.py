import streamlit as st

import sqlite3
import pandas as pd

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_table_data(database_name: str, table_name: str):
    conn = sqlite3.connect(database_name)
    orders = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
    return orders

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def get_all_tables(database_name: str):
    con = sqlite3.connect(database_name)
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table_row[0] for table_row in cursor.fetchall()]
    return tables

st.set_page_config(layout='wide')
st.title("🧳 Hummingbot Database Analyzer")
st.write("---")
uploaded_file = st.file_uploader("Add your database")

if uploaded_file is not None:
    with open(f"{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.getbuffer())
    tables = get_all_tables(uploaded_file.name)
    st.subheader("Tables of the database:")
    for table in tables:
        st.write(table)
        st.dataframe(get_table_data(uploaded_file.name, table))
