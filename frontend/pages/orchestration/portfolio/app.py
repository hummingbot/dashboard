from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient
from frontend.st_utils import initialize_st_page
import streamlit as st
import pandas as pd

initialize_st_page(title="Portfolio", icon="💰")

# Page content
client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)
NUM_COLUMNS = 4

@st.cache_data
def get_all_balances():
    return client.get_all_balances()

# Fetch all balances
balances = get_all_balances()

# Convert balances to a DataFrame for easier manipulation
def balances_to_df(balances):
    data = []
    for account, exchanges in balances.items():
        for exchange, tokens in exchanges.items():
            for token, amount in tokens.items():
                data.append({"Account": account, "Exchange": exchange, "Token": token, "Amount": amount})
    return pd.DataFrame(data)

df_balances = balances_to_df(balances)
c1, c2 = st.columns([1, 1])
with c1:
    st.header("Current Balances")
with c2:
    st.header("Aggregated Balances")

c1, c2, c3, c4 = st.columns([2.5, 1.5, 1.5, 1.1])
with c1:
    # Display balances
    st.subheader("All Balances")
    st.dataframe(df_balances)

with c2:
    # Aggregation at the account level
    account_agg = df_balances.groupby(["Account", "Token"])["Amount"].sum().reset_index()
    st.subheader("Account Level")
    st.dataframe(account_agg)

with c3:
    # Aggregation at the exchange level
    exchange_agg = df_balances.groupby(["Exchange", "Token"])["Amount"].sum().reset_index()
    st.subheader("Exchange Level")
    st.dataframe(exchange_agg)

with c4:
    # Overall holdings
    overall_agg = df_balances.groupby("Token")["Amount"].sum().reset_index()
    st.subheader("Token Level")
    st.write(overall_agg)
