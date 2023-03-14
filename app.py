# A bare bones UI for the Open AI Chat Completion used in ChatGPT
# Created by Adam Tomkins
import pydantic
pydantic.class_validators._FUNCS.clear()

import streamlit as st
from config import state_variables
from pages import *




st.title("Story Time")

key = st.sidebar.text_input("Your Open API Key", "sk...")
if key == "sk...":
    st.error("Please add a valid Open API Key in the Sidebar")

else:
    st.session_state.key = key
    openai.api_key = key

    for k,v in state_variables.items():
        if k not in st.session_state:
            st.session_state[k]=v

    pages = {
        "Main":page_generate_story,
        "Database":page_database,
        "Materials":page_create_materials
    }

    sel_page = st.sidebar.selectbox("Page", pages.keys())
    pages[sel_page]()



st.info("Created by The MicroFamily Inc.")
