# Trading Hub

The Trading Hub provides a comprehensive interface for executing trades, monitoring positions, and analyzing markets in real-time.

## Features

### 🎯 Real-time Market Data
- **OHLC Candlestick Chart**: 5-minute interval price action with volume overlay
- **Live Order Book**: Real-time bid/ask levels with configurable depth (10-100 levels)
- **Current Price Display**: Live price updates with auto-refresh capability
- **Volume Analysis**: Trading volume visualization

### ⚡ Quick Trading
- **Market Orders**: Instant buy/sell execution at current market price
- **Limit Orders**: Set specific price levels for order execution
- **Position Management**: Open/close positions for perpetual contracts
- **Multi-Exchange Support**: Trade across Binance, KuCoin, OKX, and more

### 📊 Portfolio Monitoring
- **Open Positions**: Real-time P&L tracking with entry/mark prices
- **Active Orders**: Monitor pending orders with one-click cancellation
- **Account Overview**: Multi-account position and order management

### 🔄 Auto-Refresh
- **Real-time Updates**: Configurable auto-refresh (5-second intervals)
- **Manual Refresh**: On-demand data updates
- **Live Market Data**: Continuous price and order book updates

## How to Use

### Market Selection
1. **Choose Exchange**: Select from available connectors (binance_perpetual, binance, kucoin, okx_perpetual)
2. **Select Trading Pair**: Enter the trading pair (e.g., BTC-USDT, ETH-USDT)
3. **Set Order Book Depth**: Choose how many price levels to display (10-100)

### Placing Orders
1. **Account Setup**: Specify the account name (default: master_account)
2. **Order Configuration**:
   - **Side**: Choose BUY or SELL
   - **Order Type**: Select MARKET, LIMIT, or LIMIT_MAKER
   - **Amount**: Enter the quantity to trade
   - **Price**: Set price for limit orders (auto-filled for market orders)
   - **Position Action**: Choose OPEN or CLOSE for perpetual contracts

### Managing Positions
- **View Open Positions**: Monitor unrealized P&L, entry prices, and position sizes
- **Track Performance**: Real-time updates of mark prices and P&L calculations
- **Multi-Account Support**: View positions across different trading accounts

### Order Management
- **Active Orders**: View all pending orders with real-time status
- **Bulk Cancellation**: Select multiple orders for batch cancellation
- **Order History**: Track order execution and fill status

## Technical Features

### Market Data Integration
- **Real-time Candles**: Live OHLC data with 5-minute intervals
- **Order Book Depth**: Configurable bid/ask level display
- **Price Feeds**: Live price updates across multiple exchanges
- **Volume Analysis**: Trading volume visualization and analysis

### Chart Visualization
- **Candlestick Chart**: Interactive price action with zoom and pan
- **Order Book Overlay**: Visualized bid/ask levels on the chart
- **Volume Bars**: Trading volume display below price chart
- **Dark Theme**: Futuristic styling optimized for trading environments

### Auto-Refresh System
- **Streamlit Fragments**: Efficient real-time updates without full page refresh
- **Configurable Intervals**: Adjustable refresh rates (default: 5 seconds)
- **Manual Control**: Start/stop auto-refresh as needed
- **Error Handling**: Graceful handling of connection issues

## Supported Exchanges

- **Binance Spot**: Standard spot trading
- **Binance Perpetual**: Futures and perpetual contracts
- **KuCoin**: Spot and margin trading
- **OKX Perpetual**: Futures and perpetual contracts

## Error Handling

The trading interface includes comprehensive error handling:
- **Connection Errors**: Graceful handling of backend connectivity issues
- **Order Errors**: Clear error messages for failed order placement
- **Data Errors**: Fallback displays when market data is unavailable
- **Validation**: Input validation for trading parameters

## Security Considerations

- **Account Isolation**: Each account's positions and orders are tracked separately
- **Order Validation**: Server-side validation of all trading parameters
- **Error Recovery**: Automatic retry mechanisms for transient failures
- **Safe Defaults**: Conservative default values for trading parameters