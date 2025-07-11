# Archived Bots

## Overview
The Archived Bots page provides comprehensive access to historical bot database files, enabling users to analyze past trading performance, review strategies, and extract insights from archived bot data.

## Key Features

### Database Management
- **Database Discovery**: Automatically lists all available database files in the system
- **Database Status**: Shows connection status and basic information for each database
- **Database Summary**: Provides overview statistics and metadata for each database

### Historical Data Analysis
- **Performance Metrics**: Detailed trade-based performance analysis including PnL, win/loss ratios, and key statistics
- **Trade History**: Complete record of all trades with filtering and pagination
- **Order History**: Comprehensive order book data with status filtering
- **Position Tracking**: Historical position data with timeline analysis

### Strategy Insights
- **Executor Analysis**: Review strategy executor performance and configuration
- **Controller Data**: Access to controller configurations and their historical performance
- **Strategy Comparison**: Compare different strategy implementations and their results

### Data Export & Visualization
- **Export Functionality**: Download historical data in various formats (CSV, JSON)
- **Performance Charts**: Interactive visualizations of trading performance over time
- **Comparative Analysis**: Side-by-side comparison of different archived strategies

## Usage Instructions

### 1. Database Selection
- View the list of available archived databases
- Select a database to explore its contents
- Check database status and connection health

### 2. Performance Analysis
- Navigate to the Performance tab to view trading metrics
- Review key performance indicators (KPIs)
- Analyze profit/loss trends and trading patterns

### 3. Historical Data Review
- Browse trade history with pagination controls
- Filter orders by status, date range, or trading pair
- Review position data and timeline

### 4. Strategy Analysis
- Examine executor configurations and performance
- Review controller settings and their impact
- Compare different strategy implementations

### 5. Data Export
- Select desired data range and format
- Export historical data for external analysis
- Download performance reports

## Technical Implementation

### Architecture
- **Async API Integration**: Uses nest_asyncio for async database operations
- **Database Connections**: Manages multiple database connections efficiently
- **Pagination**: Implements efficient pagination for large datasets
- **Error Handling**: Comprehensive error handling for database operations

### Components
- **Database Browser**: Interactive database selection and status display
- **Performance Dashboard**: Real-time performance metrics and charts
- **Data Grid**: Efficient display of large datasets with filtering
- **Export Manager**: Handles data export in multiple formats

### State Management
- **Database Selection**: Tracks currently selected database
- **Filter States**: Maintains filter settings across page navigation
- **Pagination State**: Manages pagination across different data views
- **Export Settings**: Remembers export preferences

### API Integration
- **ArchivedBotsRouter**: Async router for database operations
- **Batch Operations**: Efficient bulk data retrieval
- **Connection Pooling**: Manages database connections efficiently
- **Error Recovery**: Automatic retry mechanisms for failed operations

## Best Practices

### Performance Optimization
- Use pagination for large datasets
- Implement efficient filtering on the backend
- Cache frequently accessed data
- Use async operations for database queries

### User Experience
- Provide clear status indicators
- Show loading states for long operations
- Implement progressive data loading
- Offer keyboard shortcuts for navigation

### Data Integrity
- Validate database connections before operations
- Handle missing or corrupted data gracefully
- Provide clear error messages
- Implement data consistency checks

## File Structure
```
archived_bots/
├── __init__.py
├── README.md
├── app.py                 # Main application file
├── utils.py              # Utility functions
└── components/           # Page-specific components
    ├── database_browser.py
    ├── performance_dashboard.py
    ├── data_grid.py
    └── export_manager.py
```

## Dependencies
- **Backend**: ArchivedBotsRouter from hummingbot-api-client
- **Frontend**: Streamlit components, plotly for visualization
- **Utils**: nest_asyncio for async operations, pandas for data manipulation
- **Components**: Custom styling components for consistent UI