# Bot Instances Management

The Bot Instances page provides centralized control for deploying, managing, and monitoring Hummingbot trading bot instances across your infrastructure.

## Features

### 🤖 Instance Management
- **Create Bot Instances**: Deploy new Hummingbot instances with custom configurations
- **Start/Stop Control**: Manage instance lifecycle with one-click controls
- **Status Monitoring**: Real-time health checks and status updates
- **Multi-Instance Support**: Manage multiple bots running different strategies simultaneously

### 📁 Configuration Management
- **Strategy File Upload**: Deploy strategy Python files to instances
- **Script Management**: Upload and manage custom scripts
- **Configuration Templates**: Save and reuse bot configurations
- **Hot Reload**: Update strategies without restarting instances

### 🔧 Broker Management
- **Hummingbot Broker**: Start and stop the broker service
- **Connection Status**: Monitor broker health and connectivity
- **Resource Usage**: Track CPU and memory consumption
- **Log Access**: View broker logs for debugging

### 📊 Instance Monitoring
- **Performance Metrics**: Real-time P&L, trade count, and volume
- **Active Orders**: View open orders across all instances
- **Error Tracking**: Centralized error logs and alerts
- **Resource Monitoring**: CPU, memory, and network usage per instance

## Usage Instructions

### 1. Start Hummingbot Broker
- Click "Start Broker" to initialize the Hummingbot broker service
- Wait for the broker to reach "Running" status
- Verify connection by checking the status indicator

### 2. Create Bot Instance
- Click "Create New Instance" button
- Configure instance settings:
  - **Instance Name**: Unique identifier for the bot
  - **Image**: Select Hummingbot version/image
  - **Strategy**: Choose strategy file to run
  - **Credentials**: Select API keys to use
- Click "Create" to deploy the instance

### 3. Manage Strategies
- **Upload Strategy**: Use the file uploader to add new strategy files
- **Select Active Strategy**: Choose which strategy the instance should run
- **Edit Strategy**: Modify strategy parameters through the editor
- **Version Control**: Track strategy changes and rollback if needed

### 4. Control Instances
- **Start**: Launch a stopped instance
- **Stop**: Gracefully shutdown a running instance
- **Restart**: Stop and start an instance
- **Delete**: Remove an instance and its configuration

### 5. Monitor Performance
- View real-time status in the instances table
- Click on an instance for detailed metrics
- Access logs for troubleshooting
- Export performance data for analysis

## Technical Notes

### Architecture
- **Docker-based**: Each instance runs in an isolated Docker container
- **RESTful API**: Communication via Backend API Client
- **WebSocket Updates**: Real-time status updates
- **Persistent Storage**: Configurations and logs stored on disk

### Instance Lifecycle
1. **Created**: Instance configured but not running
2. **Starting**: Docker container launching
3. **Running**: Bot actively trading
4. **Stopping**: Graceful shutdown in progress
5. **Stopped**: Instance halted but configuration preserved
6. **Error**: Instance encountered fatal error

### Resource Management
- **CPU Limits**: Configurable CPU allocation per instance
- **Memory Limits**: Set maximum memory usage
- **Network Isolation**: Instances communicate only through broker
- **Storage Quotas**: Limit log and data storage per instance

## Component Structure

```
instances/
├── app.py                    # Main instances management page
├── components/
│   ├── instance_table.py     # Instance list and status display
│   ├── instance_controls.py  # Start/stop/delete controls
│   ├── broker_panel.py       # Broker management interface
│   └── strategy_uploader.py  # Strategy file management
└── utils/
    ├── docker_manager.py     # Docker container operations
    ├── instance_monitor.py   # Status polling and updates
    └── resource_tracker.py   # Resource usage monitoring
```

## Best Practices

### Instance Naming
- Use descriptive names (e.g., "btc_market_maker_01")
- Include strategy type in the name
- Add exchange identifier if running multiple exchanges
- Use consistent naming conventions

### Strategy Management
- Test strategies in paper trading first
- Keep backups of working configurations
- Document strategy parameters
- Use version control for strategy files

### Performance Optimization
- Limit instances per broker (recommended: 5-10)
- Monitor resource usage regularly
- Restart instances weekly for stability
- Clear old logs to save disk space

## Error Handling

The instances page handles various error scenarios:
- **Broker Connection Lost**: Automatic reconnection attempts
- **Instance Crashes**: Auto-restart with configurable retry limits
- **Resource Exhaustion**: Graceful degradation and alerts
- **Strategy Errors**: Detailed error logs and stack traces
- **Network Issues**: Offline mode with cached status

## Security Considerations

- **API Key Isolation**: Each instance has access only to assigned credentials
- **Network Segmentation**: Instances cannot communicate directly
- **Resource Limits**: Prevent runaway processes from affecting system
- **Audit Logging**: All actions are logged for compliance