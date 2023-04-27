# Hummingbot StreamLit Apps

Collection of Hummingbot-related data apps and dashboards, built using [StreamLit](https://streamlit.io/).

This repository is maintained by Hummingbot Foundation as a companion for users of [Hummingbot](https://github.com/hummingbot/hummingbot), the open source framework for building high-frequency crypto trading bots.

### Getting Started Video

https://www.loom.com/share/72d05bcbaf4048a399e3f9247d756a63

### Deployed Apps

https://hummingbot-streamlit-apps-main-jnja50.streamlit.app

## Current Data Apps

Here are the current data apps in the collection:

### XE Token Analyzer

Visualize the bid-ask spread and volume of different tokens across the crypto exchange landscape. This app is most helpful for Hummingbot users running the [Cross-Exchange Market Making](https://hummingbot.org/strategies/cross-exchange-market-making/) and [Arbitrage](https://hummingbot.org/strategies/arbitrage/) strategies.

### Hummingbot DB

Drop a SQLite trades file for a specific strategy configuration, so that you can inspect and analyze the trade data.

### TVL vs MCAP Analysis

Easily compare various DeFi protocols based on their market capitalization and total value locked, using DeFiLlama data.

**How to find**: These files are located in the `/data` folder in Hummingbot, and are named `<strategy_name>.sqlite`.

### Data

Reference data for the various apps this collection.

## Installation

1. Install Anaconda or Miniconda

2. Clone this repo and navigate to the created directory
```
git clone https://github.com/hummingbot/streamlit-apps.git
cd streamlit-apps
```

3. Run this command to create a `conda` environment and install dependencies
```
conda env create -f environment.yml
```

4. Activate the environment
```
conda activate streamlit-apps
```

5. Run the app
```
streamlit run main.py
```

For more info, see instructions located at https://docs.streamlit.io/library/get-started/installation.

## Contributions

We welcome new data apps, bug fixes, and improvements by the community!

To submit a contribution, issue a pull request and follow the general guidelines listed at https://hummingbot.org/developers/contributions.
