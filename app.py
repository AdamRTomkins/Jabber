# A bare bones UI for the Open AI Chat Completion used in ChatGPT
# Created by Adam Tomkins
import pydantic

pydantic.class_validators._FUNCS.clear()

import streamlit as st
from config import state_variables
from pages import *
import os


st.title("Resource Creator")

key = os.getenv("OPENAI_API_KEY", None)
if key is None:
    key = st.sidebar.text_input("Your Open API Key", "sk...")
if key == "sk...":
    st.error("Please add a valid Open API Key in the Sidebar")

else:
    st.session_state.key = key
    openai.api_key = key

    for k, v in state_variables.items():
        if k not in st.session_state:
            st.session_state[k] = v

    pages = {
        # "Main":page_generate_story,
        # "Database":page_database,
        "Characters Library": draw_character_library,
        "Resource Library": draw_resource_library,
        "Material Library": draw_material_library,
        "Create New Material": page_create_materials,
        "Create New Resource": page_create_resource,
        "Export/Restore": draw_save_session,
    }

    sel_page = st.sidebar.selectbox("Page", pages.keys())
    pages[sel_page]()


st.info("Created by The MicroFamily Inc.")
