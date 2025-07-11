import streamlit as st

from frontend.st_utils import auth_system

def main():
    # Get the navigation structure based on auth state
    pages = auth_system()
    
    # Set up navigation once
    pg = st.navigation(pages)
    
    # Run the selected page
    pg.run()


if __name__ == "__main__":
    main()
