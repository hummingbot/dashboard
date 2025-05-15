# Grid Strike Grid Component Configuration Tool

Welcome to the Grid Strike Grid Component Configuration Tool! This tool allows you to create, modify, visualize, and save configurations for the Grid Strike Grid Component trading strategy, which is a simplified version of the Grid Strike strategy focused on a single grid.

## Features

- **Simple Grid Configuration**: Configure a single grid with start, end, and limit prices.
- **Dynamic Price Range Defaults**: Automatically sets price ranges based on current market conditions.
- **Visual Grid Configuration**: See your grid settings directly on the price chart.
- **Triple Barrier Risk Management**: Configure take profit, stop loss, and time limit parameters.
- **Save and Deploy**: Once satisfied, save the configuration to deploy it later.

## How to Use

### 1. Basic Configuration

Start by configuring the basic parameters:
- **ID Prefix**: Prefix for the strategy ID (default: "grid_").
- **Trading Pair**: Choose the cryptocurrency trading pair (e.g., "BTC-FDUSD").
- **Connector Name**: Select the trading platform or exchange (e.g., "binance").
- **Leverage**: Set the leverage ratio for margin/futures trading.

### 2. Chart Configuration

Configure how you want to visualize the market data:
- **Candles Connector**: Select the data source for candlestick data.
- **Interval**: Choose the timeframe for the candlesticks (1m to 1d).
- **Days to Display**: Select how many days of historical data to show.

### 3. Grid Configuration

Configure your grid parameters:
- **Side**: Choose BUY or SELL for the grid.
- **Start Price**: The price where the grid begins.
- **End Price**: The price where the grid ends.
- **Limit Price**: A price limit that will stop the strategy.
- **Min Spread Between Orders**: Minimum price difference between orders.
- **Min Order Amount (Quote)**: Minimum size for individual orders.
- **Maximum Open Orders**: Maximum number of active orders in the grid.

### 4. Order Configuration

Fine-tune your order placement:
- **Max Orders Per Batch**: Maximum number of orders to place at once.
- **Order Frequency**: Time between order placements in seconds.
- **Activation Bounds**: Price deviation to trigger updates.

### 5. Triple Barrier Configuration

Set up risk management parameters:
- **Open Order Type**: The type of order to open positions (e.g., MARKET, LIMIT).
- **Take Profit**: Price movement percentage for take profit.
- **Stop Loss**: Price movement percentage for stop loss.
- **Time Limit**: Time limit for orders in hours.
- **Order Type Settings**: Configure order types for each barrier.

### 6. Advanced Configuration

Additional settings:
- **Position Mode**: Choose between HEDGE or ONE-WAY.
- **Strategy Time Limit**: Maximum duration for the entire strategy in hours.
- **Manual Kill Switch**: Option to enable manual kill switch.

## Understanding Grid Strike Grid Component

The Grid Strike Grid Component strategy creates a single grid of orders within a specified price range. Here's how it works:

### Grid Mechanics
- The strategy places orders uniformly between the start and end prices
- BUY grids place buy orders from start (higher) to end (lower) prices
- SELL grids place sell orders from start (lower) to end (higher) prices
- The limit price serves as an additional safety boundary

### Order Placement
- Orders are placed within the grid based on the min spread between orders
- The amount per order is calculated based on the total amount specified
- Orders are automatically adjusted when price moves beyond activation bounds

### Visual Indicators
- Green lines represent the start and end prices
- Red line represents the limit price
- Candlestick chart shows the market price action

## Example Configuration

Here's a sample configuration for a BTC-FDUSD grid:

```yaml
id: grid_btcfdusd
controller_name: grid_strike
controller_type: generic
total_amount_quote: 200
manual_kill_switch: null
candles_config: []
leverage: 75
position_mode: HEDGE
connector_name: binance
trading_pair: BTC-FDUSD
side: 1
start_price: 84000
end_price: 84300
limit_price: 83700
min_spread_between_orders: 0.0001
min_order_amount_quote: 5
max_open_orders: 40
max_orders_per_batch: 1
order_frequency: 2
activation_bounds: 0.01
triple_barrier_config:
  open_order_type: 3
  stop_loss: null
  stop_loss_order_type: 1
  take_profit: 0.0001
  take_profit_order_type: 3
  time_limit: 21600
  time_limit_order_type: 1
time_limit: 172800
```

## Best Practices

1. **Grid Placement**
   - For BUY grids, set start price above end price
   - For SELL grids, set end price above start price
   - Set limit price as a safety boundary where you want to stop the strategy

2. **Amount Management**
   - Set total amount based on your risk tolerance
   - Configure min order amount to ensure meaningful trade sizes

3. **Grid Density**
   - Adjust min spread between orders based on the asset's volatility
   - Set max open orders to control grid density

4. **Risk Management**
   - Use triple barrier parameters to manage risk for individual positions
   - Set appropriate time limits for both positions and the overall strategy 