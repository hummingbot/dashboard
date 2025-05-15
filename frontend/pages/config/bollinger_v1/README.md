# Bollinger V1 Configuration Tool

Welcome to the Bollinger V1 Configuration Tool! This tool allows you to create, modify, visualize, backtest, and save configurations for the Bollinger V1 directional trading strategy. Here’s how you can make the most out of it.

## Features

- **Start from Default Configurations**: Begin with a default configuration or use the values from an existing configuration.
- **Modify Configuration Values**: Change various parameters of the configuration to suit your trading strategy.
- **Visualize Results**: See the impact of your changes through visual charts.
- **Backtest Your Strategy**: Run backtests to evaluate the performance of your strategy.
- **Save and Deploy**: Once satisfied, save the configuration to deploy it later.

## How to Use

### 1. Load Default Configuration

Start by loading the default configuration for the Bollinger V1 strategy. This provides a baseline setup that you can customize to fit your needs.

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
- **Bollinger Bands Length**: Define the length of the Bollinger Bands.
- **Standard Deviation Multiplier**: Set the standard deviation multiplier for the Bollinger Bands.
- **Long Threshold**: Configure the threshold for long positions.
- **Short Threshold**: Configure the threshold for short positions.
- **Risk Management**: Set parameters for stop loss, take profit, time limit, and trailing stop settings.

### 3. Visualize Bollinger Bands

Visualize the Bollinger Bands on the OHLC (Open, High, Low, Close) chart to see the impact of your configuration. Here are some hints to help you fine-tune the Bollinger Bands:

- **Bollinger Bands Length**: A larger length will make the Bollinger Bands wider and smoother, while a smaller length will make them narrower and more volatile.
- **Long Threshold**: This is a reference to the Bollinger Band. A value of 0 means the lower band, and a value of 1 means the upper band. For example, if the long threshold is 0, long positions will only be taken if the price is below the lower band.
- **Short Threshold**: Similarly, a value of 1.1 means the price must be above the upper band by 0.1 of the band’s range to take a short position.
- **Thresholds**: The closer you set the thresholds to 0.5, the more trades will be executed. The farther away they are, the fewer trades will be executed.

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