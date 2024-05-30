# Super Trend Configuration Tool

Welcome to the Super Trend Configuration Tool! This tool allows you to create, modify, visualize, backtest, and save configurations for the Super Trend directional trading strategy. Here’s how you can make the most out of it.

## Features

- **Start from Default Configurations**: Begin with a default configuration or use the values from an existing configuration.
- **Modify Configuration Values**: Change various parameters of the configuration to suit your trading strategy.
- **Visualize Results**: See the impact of your changes through visual charts.
- **Backtest Your Strategy**: Run backtests to evaluate the performance of your strategy.
- **Save and Deploy**: Once satisfied, save the configuration to deploy it later.

## How to Use

### 1. Load Default Configuration

Start by loading the default configuration for the Super Trend strategy. This provides a baseline setup that you can customize to fit your needs.

### 2. User Inputs

Input various parameters for the strategy configuration. These parameters include:

- **Connector Name**: Select the trading platform or exchange.
- **Trading Pair**: Choose the cryptocurrency trading pair.
- **Leverage**: Set the leverage ratio. (Note: if you are using spot trading, set the leverage to 1)
- **Total Amount (Quote Currency)**: Define the total amount you want to allocate for trading.
- **Max Executors per Side**: Specify the maximum number of executors per side.
- **Cooldown Time**: Set the cooldown period between trades.
- **Position Mode**: Choose between different position modes.
- **Candles Connector**: Select the data source for candlestick data.
- **Candles Trading Pair**: Choose the trading pair for candlestick data.
- **Interval**: Set the interval for candlestick data.
- **Super Trend Length**: Define the length of the Super Trend indicator.
- **Super Trend Multiplier**: Set the multiplier for the Super Trend indicator.
- **Percentage Threshold**: Set the percentage threshold for signal generation.
- **Risk Management**: Set parameters for stop loss, take profit, time limit, and trailing stop settings.

### 3. Visualize Indicators

Visualize the Super Trend indicator on the OHLC (Open, High, Low, Close) chart to see the impact of your configuration. Here are some hints to help you fine-tune the indicators:

- **Super Trend Length**: A larger length will make the Super Trend indicator smoother and less sensitive to short-term price fluctuations, while a smaller length will make it more responsive to recent price changes.
- **Super Trend Multiplier**: Adjusting the multiplier affects the sensitivity of the Super Trend indicator. A higher multiplier makes the trend detection more conservative, while a lower multiplier makes it more aggressive.
- **Percentage Threshold**: This defines how close the price needs to be to the Super Trend band to generate a signal. For example, a 0.5% threshold means the price needs to be within 0.5% of the Super Trend band to consider a trade.

### Combining Super Trend and Percentage Threshold for Trade Signals

The Super Trend V1 strategy uses the Super Trend indicator combined with a percentage threshold to generate trade signals:

- **Long Signal**: The Super Trend indicator must signal a long trend, and the price must be within the percentage threshold of the Super Trend long band. For example, if the threshold is 0.5%, the price must be within 0.5% of the Super Trend long band to trigger a long trade.
- **Short Signal**: The Super Trend indicator must signal a short trend, and the price must be within the percentage threshold of the Super Trend short band. Similarly, if the threshold is 0.5%, the price must be within 0.5% of the Super Trend short band to trigger a short trade.

### 4. Executor Distribution

The total amount in the quote currency will be distributed among the maximum number of executors per side. For example, if the total amount quote is 1000 and the max executors per side is 5, each executor will have 200 to trade. If the signal is on, the first executor will place an order and wait for the cooldown time before the next one executes, continuing this pattern for the subsequent orders.

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