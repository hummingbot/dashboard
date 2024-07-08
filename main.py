import streamlit as st
from frontend.st_utils import auth_system


def main():
    # readme section
    with st.container():
        st.markdown("# 📊 hummingbot dashboard")
        st.markdown("""
            hummingbot dashboard is an open source application that helps you create, backtest, and optimize various 
            types of algo trading strategies. afterwards, you can deploy them as [hummingbot](http://hummingbot.org) 
            instances in either paper or live trading mode.""")
    st.write("---")
    st.header("Getting started")
    st.write("watch the [hummingbot dashboard tutorial playlist](https://www.youtube.com/watch?v=a-kenmqrb00) to get started!")
    video_titles = [
        "1 - introduction to dashboard",
        "2 - setting up the environment",
        "3 - managing credentials",
        "4 - using the master bot profile",
        "5 - deploying bots and running strategies",
        "7 - controllers, backtesting, and optimization",
        "8 - deploying best strategies from backtests",
        "9 - conclusions and next steps"
    ]
    # list of youtube video links
    video_links = [
        "https://www.youtube.com/embed/a-kenmqrb00",
        "https://www.youtube.com/embed/abezihb6ijg",
        "https://www.youtube.com/embed/vmld_wqve4m",
        "https://www.youtube.com/embed/mpqtnldxpno",
        "https://www.youtube.com/embed/915e-c2lwdg",
        "https://www.youtube.com/embed/bai2ok7_boo",
        "https://www.youtube.com/embed/bjf3ml-9jiq",
        "https://www.youtube.com/embed/ug_sszb2hye",
    ]
    # ensure the lists have the same length
    assert len(video_titles) == len(video_links), "mismatch between titles and links."
    with st.container():
        video_selection = st.selectbox("choose a video:", options=video_titles)
        selected_index = video_titles.index(video_selection)
        st.video(video_links[selected_index])
        st.write("---")
    st.header("feedback and issues")
    st.write("please give us feedback in the **#dashboard** channel of the [hummingbot discord](https://discord.gg/hummingbot)! 🙏")
    st.write("if you encounter any bugs or have suggestions for improvement, please create an issue in the [hummingbot dashboard github](https://github.com/hummingbot/dashboard).")

auth_system()
main()
