# Hummingbot Dashboard

Hummingbot Dashboard is an open-source application designed to assist in the creation, backtesting, and optimization of a wide variety of algorithmic trading strategies. Once refined, these strategies can be deployed as [Hummingbot](https://github.com/hummingbot/hummingbot) instances in live trading modes, providing a seamless transition from strategy formulation to actual trading execution.

## Features

- **Bot Orchestration**: Deploy and manage multiple instances of Hummingbot
- **Strategy Backtesting and Optimization**: Evaluate the performance of your strategies against historical data and optimize them with Optuna
- **One-Click Deployment**: Seamlessly deploy your strategies as Hummingbot instances for paper or live trading.
- **Performance Analysis Monitoring**: Monitor and analyze the performance of your deployed strategies.
- **Credential Management**: Create and manage separate accounts for API keys
  
## Documentation

For detailed instructions and further information, visit our [documentation page](https://hummingbot.org/dashboard/).

## Installation

Currently, we recommend users to install Dashboard using the **[Deploy repo](https://github.com/hummingbot/deploy)** instead as this will automatically launch Dashboard along with the needed components in their own Docker containers. 

If you are a developer, and want to make changes to the code then we recommend using the Source installation below - please note that you will also need to launch the Backend API and Broker separately (either through source install or through Docker).   

1. **Install Dependencies**:
   - Docker Engine
   - Miniconda or Anaconda

2. **Clone Repository and Navigate to Directory**:
    ```bash
    git clone https://github.com/hummingbot/dashboard.git
    cd dashboard
    ```

3. **Create Conda Environment and Install Dependencies**:
    ```bash
    make install
    ```

4. **Activate the Isolated 'conda' Environment**:
    ```bash
    conda activate dashboard
    ```

5. **Start the Dashboard**:
    ```bash
    make run
    ```

For more detailed instructions on how to install and update the dashboard, refer to [INSTALLATION.md](INSTALLATION.md).

## Latest Updates

Stay informed about the latest updates and enhancements to Hummingbot Dashboard by subscribing to our [newsletter](https://hummingbot.substack.com/).

## Contributing and Feedback

We welcome contributions from the community. Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

Join our [Discord](https://discord.gg/hummingbot) community to discuss strategies, ask questions, and collaborate with other Hummingbot Dashboard users:

## License

Hummingbot Dashboard is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for more details.
