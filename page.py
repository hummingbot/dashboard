import streamlit as st

class Page:
    def __init__(self, title, description, icon="🦅", layout="wide"):
        self.title = title
        self.description = description
        self.icon = icon
        self.layout = layout

    def write_page(self):
        st.set_page_config(page_title=self.title, page_icon=self.icon, layout=self.layout)
        st.title(self.title)
        st.write("---")
        with st.expander("About This Page"):
            st.write(self.description)
        st.write("---")
