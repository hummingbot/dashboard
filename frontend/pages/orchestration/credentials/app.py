from CONFIG import BACKEND_API_HOST, BACKEND_API_PORT
from backend.services.backend_api_client import BackendAPIClient
from frontend.st_utils import initialize_st_page
import streamlit as st
import pandas as pd
import plotly.express as px

initialize_st_page(title="Account Balances", icon="💰")

# Page content
client = BackendAPIClient.get_instance(host=BACKEND_API_HOST, port=BACKEND_API_PORT)

@st.cache_data(ttl=60)
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

# Aggregation at different levels
account_agg = df_balances.groupby(["Account", "Token"])["Amount"].sum().reset_index()
exchange_agg = df_balances.groupby(["Exchange", "Token"])["Amount"].sum().reset_index()
overall_agg = df_balances.groupby("Token")["Amount"].sum().reset_index()

# Display balances
st.header("Current Balances")
st.write(df_balances)

# Aggregated Balances
st.header("Aggregated Balances")
st.write(account_agg)

# Displaying account level balances
st.subheader("Account Level")
for account in account_agg["Account"].unique():
    st.write(f"**{account}**")
    df = account_agg[account_agg["Account"] == account]
    st.write(df)

# Displaying exchange level balances
st.subheader("Exchange Level")
for exchange in exchange_agg["Exchange"].unique():
    st.write(f"**{exchange}**")
    df = exchange_agg[exchange_agg["Exchange"] == exchange]
    st.write(df)

# Overall holdings
st.subheader("Overall Holdings")
st.write(overall_agg)

# Visualizations
st.header("Visualizations")

# Account level pie chart
st.subheader("Account Level Balances")
for account in account_agg["Account"].unique():
    df = account_agg[account_agg["Account"] == account]
    fig = px.pie(df, names='Token', values='Amount', title=f"Account: {account}")
    st.plotly_chart(fig)

# Exchange level bar chart
st.subheader("Exchange Level Balances")
for exchange in exchange_agg["Exchange"].unique():
    df = exchange_agg[exchange_agg["Exchange"] == exchange]
    fig = px.bar(df, x='Token', y='Amount', title=f"Exchange: {exchange}")
    st.plotly_chart(fig)

# Overall holdings pie chart
st.subheader("Overall Holdings by Token")
fig = px.pie(overall_agg, names='Token', values='Amount', title="Overall Holdings by Token")
st.plotly_chart(fig)

