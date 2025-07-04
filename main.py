import streamlit as st

from frontend.st_utils import auth_system


def patch_modules_streamlit_elements(file_path: str, old_line: str, new_line: str):
    import os


    relative_file_path = "core/callback.py"
    file_path = os.path.join(library_root, relative_file_path)

    with open(file_path, "r") as file:
        lines = file.readlines()

    is_changed = False
    for index, line in enumerate(lines):
        if old_line in line:
            print(f"Replacing line {index + 1} in {file_path}")
            lines[index] = line.replace(old_line, new_line)
            is_changed = True

    if is_changed:
        with open(file_path, "w") as file:
            file.writelines(lines)
        import importlib
        importlib.reload(streamlit_elements)

    return True

def patch_streamlit_elements():
    # # fix 1.34.0
    # patch_modules_streamlit_elements(
    #     "core/callback.py",
    #     "from streamlit.components.v1 import components",
    #     "from streamlit.components.v1 import custom_component as components\n",
    # )


    #fix 1.40.0
    patch_modules_streamlit_elements(
        "core/callback.py",
        '        user_key = kwargs.get("user_key", None)\n',
        """
        try:
            user_key = None
            new_callback_data = kwargs[
                "ctx"
            ].session_state._state._new_session_state.get(
                "streamlit_elements.core.frame.elements_frame", None
            )
            if new_callback_data is not None:
                user_key = new_callback_data._key
        except:
            user_key = None
        """.rstrip()
        + "\n",
    )


if __name__ == "__main__":
    patch_streamlit_elements()

def main():
    # Get the navigation structure based on auth state
    pages = auth_system()
    
    # Set up navigation once
    pg = st.navigation(pages)
    
    # Run the selected page
    pg.run()


if __name__ == "__main__":
    main()
