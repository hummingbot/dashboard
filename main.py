import streamlit as st

apptitle = "High Frequency Trading"
st.set_page_config(page_title=apptitle, page_icon="🦅", layout="wide")

st.title("Welcome!")
st.write("---")
st.code("💡 The purpose of this dashboard is to provide useful information for high frequency trading traders")
st.write("")
st.write("Watch this video to understand how the dashboard works! 🦅")
c1, c2, c3 = st.columns([1, 6, 1])
with c2:
    st.video("https://youtu.be/l6PWbN2pDK8")
st.write("If you want to contribute, post your idea in #dev-channel of [hummingbot discord](https://discord.gg/CjxZtkrH)")
st.write("---")




