# PMM Dynamic Configuration Tool

Welcome to the PMM Dynamic Configuration Tool! This tool allows you to create, modify, visualize, backtest, and save configurations for the PMM Dynamic trading strategy. Here’s how you can make the most out of it.

## Features

- **Start from Default Configurations**: Begin with a default configuration or use the values from an existing configuration.
- **Modify Configuration Values**: Change various parameters of the configuration to suit your trading strategy.
- **Visualize Results**: See the impact of your changes through visual charts, including indicators like MACD and NATR.
- **Backtest Your Strategy**: Run backtests to evaluate the performance of your strategy.
- **Save and Deploy**: Once satisfied, save the configuration to deploy it later.

## How to Use

### 1. Load Default Configuration

Start by loading the default configuration for the PMM Dynamic strategy. This provides a baseline setup that you can customize to fit your needs.

### 2. User Inputs

Input various parameters for the strategy configuration. These parameters include:

- **Connector Name**: Select the trading platform or exchange.
- **Trading Pair**: Choose the cryptocurrency trading pair.
- **Leverage**: Set the leverage ratio. (Note: if you are using spot trading, set the leverage to 1)
- **Total Amount (Quote Currency)**: Define the total amount you want to allocate for trading.
- **Position Mode**: Choose between different position modes.
- **Cooldown Time**: Set the cooldown period between trades.
- **Executor Refresh Time**: Define how often the executors refresh.
- **Candles Connector**: Select the data source for candlestick data.
- **Candles Trading Pair**: Choose the trading pair for candlestick data.
- **Interval**: Set the interval for candlestick data.
- **MACD Fast Period**: Set the fast period for the MACD indicator.
- **MACD Slow Period**: Set the slow period for the MACD indicator.
- **MACD Signal Period**: Set the signal period for the MACD indicator.
- **NATR Length**: Define the length for the NATR indicator.
- **Risk Management**: Set parameters for stop loss, take profit, time limit, and trailing stop settings.

### 3. Indicator Visualization

Visualize the candlestick data along with the MACD and NATR indicators. This helps you understand how the MACD will shift the mid-price and how the NATR will be used as a base multiplier for spreads.

### 4. Executor Distribution

The distribution of orders is now a multiplier of the base spread, which is determined by the NATR indicator. This allows the algorithm to adapt to changing market conditions by adjusting the spread based on the average size of the candles.

### 5. Backtesting

Run backtests to evaluate the performance of your configured strategy. The backtesting section allows you to:

- **Process Data**: Analyze historical trading data.
- **Visualize Results**: See performance metrics and charts.
- **Evaluate Accuracy**: Assess the accuracy of your strategy’s predictions and trades.
- **Understand Close Types**: Review different types of trade closures and their frequencies.

### 6. Save Configuration

Once you are satisfied with your configuration and backtest results, save the configuration for future use in the Deploy tab. This allows you to deploy the same strategy later without having to reconfigure it from scratch.

---

Feel free to experiment with different configurations to find the optimal setup for your trading strategy. Happy trading!