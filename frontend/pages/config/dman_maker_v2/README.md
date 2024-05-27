# D-Man Maker V2 Configuration Tool

Welcome to the D-Man Maker V2 Configuration Tool! This tool allows you to create, modify, visualize, backtest, and save configurations for the D-Man Maker V2 trading strategy. Here’s how you can make the most out of it.

## Features

- **Start from Default Configurations**: Begin with a default configuration or use the values from an existing configuration.
- **Modify Configuration Values**: Change various parameters of the configuration to suit your trading strategy.
- **Visualize Results**: See the impact of your changes through visual charts.
- **Backtest Your Strategy**: Run backtests to evaluate the performance of your strategy.
- **Save and Deploy**: Once satisfied, save the configuration to deploy it later.

## How to Use

### 1. Load Default Configuration

Start by loading the default configuration for the D-Man Maker V2 strategy. This provides a baseline setup that you can customize to fit your needs.

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
- **Custom D-Man Maker V2 Settings**: Set specific parameters like top executor refresh time and activation bounds.

### 3. Executor Distribution Visualization

Visualize the distribution of your trading executors. This helps you understand how your buy and sell orders are spread across different price levels and amounts.

### 4. DCA Distribution

After setting the executor distribution, you will need to configure the internal distribution of the DCA (Dollar Cost Averaging). This involves multiple open orders and one close order per executor level. Visualize the DCA distribution to see how the entry prices are spread and ensure the initial DCA order amounts are above the minimum order size of the exchange.

### 5. Risk Management

Configure risk management settings, including take profit, stop loss, time limit, and trailing stop settings for each DCA. This step is crucial for managing your trades and minimizing risk.

### 6. Backtesting

Run backtests to evaluate the performance of your configured strategy. The backtesting section allows you to:

- **Process Data**: Analyze historical trading data.
- **Visualize Results**: See performance metrics and charts.
- **Evaluate Accuracy**: Assess the accuracy of your strategy’s predictions and trades.
- **Understand Close Types**: Review different types of trade closures and their frequencies.

### 7. Save Configuration

Once you are satisfied with your configuration and backtest results, save the configuration for future use in the Deploy tab. This allows you to deploy the same strategy later without having to reconfigure it from scratch.

---

Feel free to experiment with different configurations to find the optimal setup for your trading strategy. Happy trading!