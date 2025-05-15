# XEMM Configuration Tool

Welcome to the XEMM Configuration Tool! This tool allows you to create, modify, visualize, backtest, and save configurations for the XEMM (Cross-Exchange Market Making) strategy. Here’s how you can make the most out of it.

## Features

- **Start from Default Configurations**: Begin with a default configuration or use the values from an existing configuration.
- **Modify Configuration Values**: Change various parameters of the configuration to suit your trading strategy.
- **Visualize Results**: See the impact of your changes through visual charts.
- **Backtest Your Strategy**: Run backtests to evaluate the performance of your strategy.
- **Save and Deploy**: Once satisfied, save the configuration to deploy it later.

## How to Use

### 1. Load Default Configuration

Start by loading the default configuration for the XEMM strategy. This provides a baseline setup that you can customize to fit your needs.

### 2. User Inputs

Input various parameters for the strategy configuration. These parameters include:

- **Maker Connector**: Select the maker trading platform or exchange where limit orders will be placed.
- **Maker Trading Pair**: Choose the trading pair on the maker exchange.
- **Taker Connector**: Select the taker trading platform or exchange where market orders will be executed to hedge the imbalance.
- **Taker Trading Pair**: Choose the trading pair on the taker exchange.
- **Min Profitability**: Set the minimum profitability percentage at which orders will be refreshed to avoid risking liquidity.
- **Max Profitability**: Set the maximum profitability percentage at which orders will be refreshed to avoid being too far from the mid-price.
- **Buy Maker Levels**: Specify the number of buy maker levels.
- **Buy Targets and Amounts**: Define the target profitability and amounts for each buy maker level.
- **Sell Maker Levels**: Specify the number of sell maker levels.
- **Sell Targets and Amounts**: Define the target profitability and amounts for each sell maker level.

### 3. Visualize Order Distribution

Visualize the order distribution with profitability targets using Plotly charts. This helps you understand how your buy and sell orders are distributed across different profitability levels.

### Min and Max Profitability

The XEMM strategy uses min and max profitability bounds to manage the placement of limit orders:

- **Min Profitability**: If the expected profitability of a limit order drops below this value, the order will be refreshed to avoid risking liquidity.
- **Max Profitability**: If the expected profitability of a limit order exceeds this value, the order will be refreshed to avoid being too far from the mid-price.

### Combining Profitability Targets and Order Amounts

- **Buy Orders**: Configure the target profitability and amounts for each buy maker level. The orders will be refreshed if they fall outside the min and max profitability bounds.
- **Sell Orders**: Similarly, configure the target profitability and amounts for each sell maker level, with orders being refreshed based on the profitability bounds.

### 4. Save and Download Configuration

Once you have configured your strategy, you can save and download the configuration as a YAML file. This allows you to deploy the strategy later without having to reconfigure it from scratch.

### 5. Upload Configuration to Backend API

You can also upload the configuration directly to the Backend API for immediate deployment. This ensures that your strategy is ready to be executed in real-time.

## Conclusion

By following these steps, you can efficiently configure your XEMM strategy, visualize its potential performance, and deploy it for trading. Feel free to experiment with different configurations to find the optimal setup for your trading needs. Happy trading!