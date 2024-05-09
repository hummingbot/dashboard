# D-Man Maker V2

## Features
- **Interactive Configuration**: Configure market making parameters such as spreads, amounts, and order levels through an intuitive web interface.
- **Visual Feedback**: Visualize order spread and amount distributions using dynamic Plotly charts.
- **Backend Integration**: Save and deploy configurations directly to a backend system for active management and execution.

### Using the Tool
1. **Configure Parameters**: Use the Streamlit interface to input parameters such as connector type, trading pair, and leverage.
2. **Set Distributions**: Define distributions for buy and sell orders, including spread and amount, either manually or through predefined distribution types like Geometric or Fibonacci.
3. **Visualize Orders**: View the configured order distributions on a Plotly graph, which illustrates the relationship between spread and amount.
4. **Export Configuration**: Once the configuration is set, export it as a YAML file or directly upload it to the Backend API.
5. **Upload**: Use the "Upload Config to BackendAPI" button to send your configuration to the backend system. Then can be used to deploy a new bot.

## Troubleshooting
- **UI Not Loading**: Ensure all Python dependencies are installed and that the Streamlit server is running correctly.
- **API Errors**: Check the console for any error messages that may indicate issues with the backend connection.

For more detailed documentation on the backend API and additional configurations, please refer to the project's documentation or contact the development team.