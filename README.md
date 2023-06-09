# Hummingbot Dashboard

Collection of Hummingbot-related dashboards, built using [StreamLit](https://streamlit.io/).

This repository is maintained by Hummingbot Foundation as a companion for users of [Hummingbot](https://github.com/hummingbot/hummingbot), the open source framework for building high-frequency crypto trading bots.

Watch this video to understand how it works:
https://www.loom.com/share/72d05bcbaf4048a399e3f9247d756a63

See an example of a live, deployed dashboard:
https://hummingbot-streamlit-app-main-jnja50.streamlit.app

## Dashboards

Here are the current dashboards in the collection:

### 🚀 Strategy Performance (WIP)

Dashboard that helps you analyze the performance of a running Hummingbot instance

### 🧙 XE Token Analyzer

Dashboard that helps you visualize the bid-ask spread and volume of different tokens across the crypto exchange landscape. 

This app is most helpful for Hummingbot users running the [Cross-Exchange Market Making](https://hummingbot.org/strategies/cross-exchange-market-making/) and [Arbitrage](https://hummingbot.org/strategies/arbitrage/) strategies.

### 🧳 Hummingbot DB

Inspect and analyze the orders and trades data contained in a SQLite database for a strategy or script. 

These files are located in the `/data` folder in Hummingbot, and are named `<strategy_name>.sqlite`.

### 🦉 TVL vs MCAP Analysis

Easily compare various DeFi protocols based on their market capitalization and total value locked, using DeFiLlama data.

### 🗂 Candles Downloader

Download historical exchange data as OHLVC candles. Supports multiple trading pairs and custom time ranges/intervals.

Current Hummingbot connectors supported:
* `binance`
* `binance_perpetual`

### 📋 Data

Reference data for the various apps this collection.

## Installation

1. Install [Anaconda](https://www.anaconda.com/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

2. Clone this repo and navigate to the created directory
```bash
git clone https://github.com/hummingbot/dashboard.git
cd dashboard
```

3. Run this command to create a `conda` environment and install dependencies
```
conda env create -f environment_conda.yml
```

4. Activate the environment
```bash
conda activate dashboard
```

5. Run the app
```bash
streamlit run main.py
```

6. Create a symlink to your Hummingbot `/data` directory
```bash
# replace `/path/to/hummingbot` with the actual path
ln -s /path/to/hummingbot/data data
```

For more info about Streamlit installation, see the instructions located at https://docs.streamlit.io/library/get-started/installation.

## Updates

To update the `dashboard` environment for new dependencies, run:
```
conda env update -f environment_conda.yml
```

## Contributions

We welcome new data apps, bug fixes, and improvements by the community!

To submit a contribution, issue a pull request, following the guidelines listed at https://hummingbot.org/developers/contributions.
