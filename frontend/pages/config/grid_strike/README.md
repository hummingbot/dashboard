# Grid Strike Configuration Tool

Welcome to the Grid Strike Configuration Tool! This tool allows you to create, modify, visualize, and save configurations for the Grid Strike trading strategy. Here's how you can make the most out of it.

## Features

- **Start from Default Configurations**: Begin with a default configuration or use the values from an existing configuration.
- **Dynamic Price Range Defaults**: Automatically sets grid ranges based on current market conditions.
- **Visual Grid Configuration**: See your grid ranges directly on the price chart.
- **Multiple Grid Ranges**: Configure up to 5 different grid ranges with different sides (BUY/SELL).
- **Save and Deploy**: Once satisfied, save the configuration to deploy it later.

## How to Use

### 1. Basic Configuration

Start by configuring the basic parameters:
- **Connector Name**: Select the trading platform or exchange (e.g., "binance").
- **Trading Pair**: Choose the cryptocurrency trading pair (e.g., "BTC-USDT").
- **Leverage**: Set the leverage ratio (use 1 for spot trading).

### 2. Chart Configuration

Configure how you want to visualize the market data:
- **Candles Connector**: Select the data source for candlestick data.
- **Interval**: Choose the timeframe for the candlesticks (1m to 1d).
- **Days to Display**: Select how many days of historical data to show.

### 3. Grid Ranges

Configure up to 5 grid ranges with different parameters:
- **Number of Grid Ranges**: Select how many ranges you want to configure (1-5).
- **Side**: Choose BUY or SELL for each range.
- **Start Price**: The price where the range begins.
- **End Price**: The price where the range ends.
- **Amount %**: Percentage of total amount allocated to this range.

### 4. Advanced Configuration

Fine-tune your strategy with advanced parameters:
- **Position Mode**: Choose between HEDGE or ONE-WAY.
- **Time Limit**: Maximum duration for orders (in hours).
- **Activation Bounds**: Price deviation to trigger updates.
- **Min Spread Between Orders**: Minimum price difference between orders.
- **Min Order Amount**: Minimum size for individual orders.
- **Max Open Orders**: Maximum number of active orders per range.
- **Grid Range Update Interval**: How often to update grid ranges (in seconds).

## Understanding Grid Strike Strategy

The Grid Strike strategy creates a grid of orders within specified price ranges. Here's how it works:

### Grid Range Mechanics
- Each grid range defines a price zone where the strategy will place orders
- BUY ranges place buy orders from higher to lower prices
- SELL ranges place sell orders from lower to higher prices
- Multiple ranges can work simultaneously with different configurations

### Order Placement
- Orders are placed within each range based on the min spread between orders
- The amount per order is calculated based on the range's allocation percentage
- Orders are automatically adjusted when price moves beyond activation bounds

### Visual Indicators
- Green lines represent BUY ranges
- Red lines represent SELL ranges
- Different dash patterns distinguish multiple ranges of the same side
- Horizontal lines show the start and end prices of each range

## Best Practices

1. **Range Placement**
   - Place BUY ranges below current price
   - Place SELL ranges above current price
   - Avoid overlapping ranges of the same side

2. **Amount Allocation**
   - Distribute amounts across ranges based on your risk preference
   - Ensure total allocation across all ranges doesn't exceed 100%
   - Consider larger allocations for ranges closer to current price

3. **Spread Configuration**
   - Set min spread based on the asset's volatility
   - Larger spreads mean fewer, more profitable orders
   - Smaller spreads mean more frequent, less profitable orders

4. **Risk Management**
   - Use appropriate leverage (1 for spot)
   - Set reasonable time limits for orders
   - Monitor and adjust activation bounds based on market conditions

## Example Configuration

Here's a sample configuration for a BTC-USDT grid:
