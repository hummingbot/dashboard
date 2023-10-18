# Hummingbot Dashboard

Hummingbot Dashboard is an open-source application designed to assist in the creation, backtesting, and optimization of a wide variety of algorithmic trading strategies. Once refined, these strategies can be deployed as [Hummingbot](https://github.com/hummingbot/hummingbot) instances in either paper trading or live trading modes, providing a seamless transition from strategy formulation to actual trading execution.

## Features

- **Bot Orchestration**: Deploy and manage multiple instances of Hummingbot
- **Strategy Backtesting and Optimization**: Evaluate the performance of your strategies against historical data and optimize them with Optuna
- **One-Click Deployment**: Seamlessly deploy your strategies as Hummingbot instances for paper or live trading.
- **Performance Analysis Monitoring**: Monitor and analyze the performance of your deployed strategies.
- **Secure Credentials**: Restrict access to whitelisted users
  
## Tutorial

Get a comprehensive understanding of Hummingbot Dashboard by exploring our introductory video playlist. These videos will guide you through the various features and functionalities:

1. [Introduction to Dashboard](https://www.youtube.com/watch?v=a-kenMqRB00&list=PLDwlNkL_4MMf0Ifvj-HLuQ_Jtf7OV6uzW&index=1)
2. [Setting up the Environment](https://www.youtube.com/watch?v=AbezIhb6iJg&list=PLDwlNkL_4MMf0Ifvj-HLuQ_Jtf7OV6uzW&index=2)
3. [Managing Credentials](https://www.youtube.com/watch?v=VmlD_WQVe4M&list=PLDwlNkL_4MMf0Ifvj-HLuQ_Jtf7OV6uzW&index=3)
4. [Using the Master Bot Profile](https://www.youtube.com/watch?v=MPQTnlDXPno&list=PLDwlNkL_4MMf0Ifvj-HLuQ_Jtf7OV6uzW&index=4)
5. [Deploying Bots and Running Strategies](https://www.youtube.com/watch?v=915E-C2LWdg&list=PLDwlNkL_4MMf0Ifvj-HLuQ_Jtf7OV6uzW&index=5)
6. Analyzing Strategy Performance (coming soon)
7. [Controllers, Backtesting, and Optimization](https://www.youtube.com/watch?v=bAi2ok7_boo&list=PLDwlNkL_4MMf0Ifvj-HLuQ_Jtf7OV6uzW&index=6)
8. [Deploying Best Strategies from Backtests](https://www.youtube.com/watch?v=BJf3ml-9JIQ&list=PLDwlNkL_4MMf0Ifvj-HLuQ_Jtf7OV6uzW&index=7)
9. [Conclusions and Next Steps](https://www.youtube.com/watch?v=ug_SSZb2HYE&list=PLDwlNkL_4MMf0Ifvj-HLuQ_Jtf7OV6uzW&index=8)

## Documentation

For detailed instructions and further information, visit our [documentation page](https://hummingbot.org/dashboard/).

## Installation

Currently, Dashboard should be installed from source via the process below. In the future, we aim to support a simpler,Docker-based installation process as well.

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
    make env_create
    ```

4. **Activate the Isolated 'conda' Environment**:
    ```bash
    conda activate dashboard
    ```

5. **Start the Dashboard**:
    ```bash
    streamlit run main.py
    ```

For more detailed instructions on how to install and update the dashboard, refer to [INSTALLATION.md](INSTALLATION.md).

## Latest Updates

Stay informed about the latest updates and enhancements to Hummingbot Dashboard by subscribing to our [newsletter](https://hummingbot.substack.com/).

## Contributing and Feedback

We welcome contributions from the community. Please read our [contributing guidelines](CONTRIBUTING.md) to get started.

Join our [Discord](https://discord.gg/hummingbot) community to discuss strategies, ask questions, and collaborate with other Hummingbot Dashboard users:

## License

Hummingbot Dashboard is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for more details.
