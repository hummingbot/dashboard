from binance.client import Client
import streamlit as st
from datetime import datetime, timedelta

# Replace the following values with your actual API keys obtained on Binance
account_names = ["Dolm","xxx"]
api_keys = [
    '93UFElCptbUDRwFZ5e91Tp3s2ZBP3xAaTK957Ay1b1nrIpgOiVy1vOy5boO8hadR','xxx_api_keys'
]
api_secrets = [
    'KQvkxk2D6nHK3Lk0xphH9mxg8wtaO8IvbDwdRFh2fpGIJVTc3v7SSxF6VWGS1PxN',"xxx_api_secrets"
]

# Initialize Binance clients
clients = [Client(api_key, api_secret) for api_key, api_secret in zip(api_keys, api_secrets)]

# Aggregate USDT balances, total trade volumes in the last three days, unrealized PNL, and PNL in the last three days for multiple Binance accounts
st.title('Leaderboard')
account_data = []

for client, account_name in zip(clients, account_names):
    # Get account USDT balance
    account_info = client.futures_account_balance()
    usdt_balance = float(next((balance['balance'] for balance in account_info if balance['asset'] == 'USDT'), None))

    # Get account position information
    positions = client.futures_position_information()
    unrealized_pnl = sum(float(position['unRealizedProfit']) for position in positions)

    # Calculate the total balance of USDT and unrealized PNL
    total_balance = usdt_balance + unrealized_pnl

    # Get all trades in the last three days
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - 3 * 24 * 60 * 60 * 1000
    trades = client.futures_account_trades(startTime=start_time, endTime=end_time)

    # Calculate the total trade volume in the last three days
    total_trade_volume = sum(float(trade['quoteQty']) for trade in trades)

    # Get PNL in the last three days
    pnl_records = client.futures_income_history(startTime=start_time, endTime=end_time, limit=1000)

    # Filter out transfer records and calculate total PNL
    total_pnl = 0
    for record in pnl_records:
        if record['incomeType'] != 'TRANSFER':
            total_pnl += float(record['income'])

    # Combine all information
    account_data.append({
        "Name": account_name,
        "Balance": usdt_balance,
        "Realized PNL": total_pnl,
        "Unrealized PNL": unrealized_pnl,
        "PNL": total_pnl + unrealized_pnl,
        "Volume": total_trade_volume,
    })

# Display all information in a table
st.table(account_data)
