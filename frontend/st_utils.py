import os.path

import pandas as pd
from pathlib import Path
import inspect

import streamlit as st
from st_pages import add_page_title

def initialize_st_page(title: str, icon: str, layout="wide", initial_sidebar_state="collapsed"):
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state
    )
    caller_frame = inspect.currentframe().f_back

    add_page_title(layout=layout, initial_sidebar_state=initial_sidebar_state)

    current_directory = Path(os.path.dirname(inspect.getframeinfo(caller_frame).filename))
    readme_path = current_directory / "README.md"
    with st.expander("About This Page"):
        st.write(readme_path.read_text())


def download_csv_button(df: pd.DataFrame, filename: str, key: str):
    csv = df.to_csv(index=False).encode('utf-8')
    return st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{filename}.csv",
                mime="text/csv",
                key=key
            )


def style_metric_cards(
    background_color: str = "rgba(255, 255, 255, 0)",
    border_size_px: int = 1,
    border_color: str = "rgba(255, 255, 255, 0.3)",
    border_radius_px: int = 5,
    border_left_color: str = "rgba(255, 255, 255, 0.5)",
    box_shadow: bool = True,
):

    box_shadow_str = (
        "box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;"
        if box_shadow
        else "box-shadow: none !important;"
    )
    st.markdown(
        f"""
        <style>
            div[data-testid="metric-container"] {{
                background-color: {background_color};
                border: {border_size_px}px solid {border_color};
                padding: 5% 5% 5% 10%;
                border-radius: {border_radius_px}px;
                border-left: 0.5rem solid {border_left_color} !important;
                {box_shadow_str}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

