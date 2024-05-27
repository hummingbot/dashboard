# PMM Simple Configuration Tool

Welcome to the PMM Simple Configuration Tool! This tool allows you to create, modify, visualize, backtest, and save configurations for the PMM Simple trading strategy. Here’s how you can make the most out of it.

## Features

- **Start from Default Configurations**: Begin with a default configuration or use the values from an existing configuration.
- **Modify Configuration Values**: Change various parameters of the configuration to suit your trading strategy.
- **Visualize Results**: See the impact of your changes through visual charts.
- **Backtest Your Strategy**: Run backtests to evaluate the performance of your strategy.
- **Save and Deploy**: Once satisfied, save the configuration to deploy it later.

## How to Use

### 1. Load Default Configuration

Start by loading the default configuration for the PMM Simple strategy. This provides a baseline setup that you can customize to fit your needs.

### 2. User Inputs

Input various parameters for the strategy configuration. These parameters include:

- **Connector Name**: Select the trading platform or exchange.
- **Trading Pair**: Choose the cryptocurrency trading pair.
- **Leverage**: Set the leverage ratio. (Note: if you are using spot trading, set the leverage to 1)
- **Total Amount (Quote Currency)**: Define the total amount you want to allocate for trading.
- **Position Mode**: Choose between different position modes.
- **Cooldown Time**: Set the cooldown period between trades.
- **Executor Refresh Time**: Define how often the executors refresh.
- **Buy/Sell Spread Distributions**: Configure the distribution of buy and sell spreads.
- **Order Amounts**: Specify the percentages for buy and sell order amounts.
- **Risk Management**: Set parameters for stop loss, take profit, time limit, and trailing stop settings.

### 3. Executor Distribution Visualization

Visualize the distribution of your trading executors. This helps you understand how your buy and sell orders are spread across different price levels and amounts.

### 4. Backtesting

Run backtests to evaluate the performance of your configured strategy. The backtesting section allows you to:

- **Process Data**: Analyze historical trading data.
- **Visualize Results**: See performance metrics and charts.
- **Evaluate Accuracy**: Assess the accuracy of your strategy’s predictions and trades.
- **Understand Close Types**: Review different types of trade closures and their frequencies.

### 5. Save Configuration

Once you are satisfied with your configuration and backtest results, save the configuration for future use in the Deploy tab. This allows you to deploy the same strategy later without having to reconfigure it from scratch.