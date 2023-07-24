import os.path
from pathlib import Path
import inspect

import streamlit as st


def initialize_st_page(title: str, icon: str, layout="wide"):
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
    )
    st.title(f"{icon} {title}")
    caller_frame = inspect.currentframe().f_back

    current_directory = Path(os.path.dirname(inspect.getframeinfo(caller_frame).filename))
    readme_path = current_directory / "README.md"
    with st.expander("About This Page"):
        st.write(readme_path.read_text())
