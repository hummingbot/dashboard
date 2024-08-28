import streamlit as st

from frontend.st_utils import auth_system


def main():
    # readme section
    st.markdown("# 📊 Hummingbot Dashboard")
    st.markdown("Hummingbot Dashboard is an open source application that helps you create, backtest, and optimize "
                "various types of algo trading strategies. Afterwards, you can deploy them as "
                "[Hummingbot](http://hummingbot.org)")
    st.write("---")
    st.header("Watch the Hummingbot Dashboard Tutorial!")
    st.video("https://youtu.be/7eHiMPRBQLQ?si=PAvCq0D5QDZz1h1D")
    st.header("Feedback and issues")
    st.write(
        "Please give us feedback in the **#dashboard** channel of the "
        "[hummingbot discord](https://discord.gg/hummingbot)! 🙏")
    st.write(
        "If you encounter any bugs or have suggestions for improvement, please create an issue in the "
        "[hummingbot dashboard github](https://github.com/hummingbot/dashboard).")


auth_system()
main()
