import streamlit as st
from pathlib import Path
from page import Page

class HummingbotDashboardPage(Page):
    def __init__(self):
        super().__init__("Hummingbot Dashboard", Path("README.md").read_text())

    def write_page(self):
        super().write_page()
        st.code("💡 The purpose of this dashboard is to provide useful information for high frequency trading traders")
        st.write("")
        st.write("Watch this video to understand how the dashboard works! 🦅")
        c1, c2, c3 = st.columns([1, 6, 1])
        with c2:
            st.video("https://youtu.be/l6PWbN2pDK8")
        st.write("If you want to contribute, post your idea in #dev-channel of [hummingbot discord](https://discord.gg/CjxZtkrH)")

if __name__ == "__main__":
    page = HummingbotDashboardPage()
    page.write_page()