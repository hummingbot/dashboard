import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.st_utils import get_backend_api_client, initialize_st_page

initialize_st_page(title="Portfolio", icon="💰")

# Page content
client = get_backend_api_client()
NUM_COLUMNS = 4


# Convert balances to a DataFrame for easier manipulation
def account_state_to_df(account_state):
    data = []
    for account, exchanges in account_state.items():
        for exchange, tokens_info in exchanges.items():
            for info in tokens_info:
                data.append({
                    "account": account,
                    "exchange": exchange,
                    "token": info["token"],
                    "price": info["price"],
                    "units": info["units"],
                    "value": info["value"],
                    "available_units": info["available_units"],
                })
    return pd.DataFrame(data)


# Convert historical account states to a DataFrame
def account_history_to_df(history):
    data = []
    for record in history:
        timestamp = record["timestamp"]
        for account, exchanges in record["state"].items():
            for exchange, tokens_info in exchanges.items():
                for info in tokens_info:
                    data.append({
                        "timestamp": timestamp,
                        "account": account,
                        "exchange": exchange,
                        "token": info["token"],
                        "price": info["price"],
                        "units": info["units"],
                        "value": info["value"],
                        "available_units": info["available_units"],
                    })
    return pd.DataFrame(data)


# Fetch account state from the backend
account_state = client.get_accounts_state()
account_history = client.get_account_state_history()
if len(account_state) == 0:
    st.warning("No accounts found.")
    st.stop()

# Display the accounts available
accounts = st.multiselect("Select Accounts", list(account_state.keys()), list(account_state.keys()))
if len(accounts) == 0:
    st.warning("Please select an account.")
    st.stop()

# Display the exchanges available
exchanges_available = []
for account in accounts:
    exchanges_available += account_state[account].keys()

if len(exchanges_available) == 0:
    st.warning("No exchanges found.")
    st.stop()
exchanges = st.multiselect("Select Exchanges", exchanges_available, exchanges_available)

# Display the tokens available
tokens_available = []
for account in accounts:
    for exchange in exchanges:
        if exchange in account_state[account]:
            tokens_available += [info["token"] for info in account_state[account][exchange]]

token_options = set(tokens_available)
tokens_available = st.multiselect("Select Tokens", token_options, token_options)


st.write("---")

filtered_account_state = {}
for account in accounts:
    filtered_account_state[account] = {}
    for exchange in exchanges:
        if exchange in account_state[account]:
            filtered_account_state[account][exchange] = [token_info for token_info in account_state[account][exchange]
                                                         if token_info["token"] in tokens_available]

filtered_account_history = []
for record in account_history:
    filtered_record = {"timestamp": record["timestamp"], "state": {}}
    for account in accounts:
        if account in record["state"]:
            filtered_record["state"][account] = {}
            for exchange in exchanges:
                if exchange in record["state"][account]:
                    filtered_record["state"][account][exchange] = [token_info for token_info in
                                                                   record["state"][account][exchange] if
                                                                   token_info["token"] in tokens_available]
    filtered_account_history.append(filtered_record)

if len(filtered_account_state) > 0:
    account_state_df = account_state_to_df(filtered_account_state)
    total_balance_usd = round(account_state_df["value"].sum(), 2)
    c1, c2 = st.columns([1, 5])
    with c1:
        st.metric("Total Balance (USD)", total_balance_usd)
    with c2:
        account_state_df['% Allocation'] = (account_state_df['value'] / total_balance_usd) * 100
        account_state_df['label'] = account_state_df['token'] + ' ($' + account_state_df['value'].apply(
            lambda x: f'{x:,.2f}') + ')'

        # Create a sunburst chart with Plotly Express
        fig = px.sunburst(account_state_df,
                          path=['account', 'exchange', 'label'],
                          values='value',
                          hover_data={'% Allocation': ':.2f'},
                          title='% Allocation by Account, Exchange, and Token',
                          color='account',
                          color_discrete_sequence=px.colors.qualitative.Vivid)

        fig.update_traces(textinfo='label+percent entry')

        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=800, title_x=0.01, title_y=1,)

        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(account_state_df[['exchange', 'token', 'units', 'price', 'value', 'available_units']], width=1800,
                 height=600)

# Plot the evolution of the portfolio over time
if len(filtered_account_history) > 0:
    account_history_df = account_history_to_df(filtered_account_history)
    account_history_df['timestamp'] = pd.to_datetime(account_history_df['timestamp'], format='ISO8601')

    # Aggregate the value of the portfolio over time
    portfolio_evolution_df = account_history_df.groupby('timestamp')['value'].sum().reset_index()

    fig = px.line(portfolio_evolution_df, x='timestamp', y='value', title='Portfolio Evolution Over Time')
    fig.update_layout(xaxis_title='Time', yaxis_title='Total Value (USD)', height=600)
    st.plotly_chart(fig, use_container_width=True)

    # Plot the evolution of each token's value over time
    token_evolution_df = account_history_df.groupby(['timestamp', 'token'])['value'].sum().reset_index()

    fig = px.area(token_evolution_df, x='timestamp', y='value', color='token', title='Token Value Evolution Over Time',
                  color_discrete_sequence=px.colors.qualitative.Vivid)
    fig.update_layout(xaxis_title='Time', yaxis_title='Value (USD)', height=600)
    st.plotly_chart(fig, use_container_width=True)
