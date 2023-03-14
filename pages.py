import streamlit as st
from io import StringIO
import json
import openai
import pandas as pd

from data import (
    characters, hobbies, likes, dislikes, destination, adults, tense
)

from prompts import *

from models import Character, Resource, ResourceRequirements, Workspace
from core_utils import generate_materials

def extract_requirements(resource):
    characters = {}
    properties = {}
    
    st.subheader("Characters")
    for char in resource.slots.characters:        
        characters[char] = st.selectbox(char, st.session_state.database["characters"])
    
    st.subheader("Properties")

    for prop, values in resource.slots.properties.items():
        properties[prop] = st.selectbox(prop, values)

    return ResourceRequirements(characters=characters, properties=properties)
    

def page_create_materials():

    # 1. Select the Resource you want.
    resources = {r.name:r for r in st.session_state.database["resources"]}

    resource_name = st.selectbox("Resource Name", resources.keys())
    resource = resources[resource_name]
    st.write(resource.description)
    with st.expander("Resource Config"):
        st.write(resource)

    # 2. Extract the requirements
    # 3. Filfil the requirements
    mat_name = st.text_input("Material Name")
    mat_description = st.text_input("Material Description")
    requirements = extract_requirements(resource)
       
    if st.button("Generate"):
    # 4. Execute the resource
        workspace = Workspace(
            id = "1",
            characters = st.session_state.database["characters"],
            available_tasks = []
        )
        materials = generate_materials(workspace=workspace, resource=resource, requirements=requirements, name=mat_name, description=mat_description)

        st.write(materials.name)
        st.write(materials.description)

        for k,v in materials.data.items():
            st.write(f"_{k}_")
            st.write(f"{v}")

        # 5. Save the Resource
        st.session_state.database["materials"].append(materials)


def draw_character(character):
    st.write(character)

def draw_character_library():
    st.subheader("Resource")

    for c in st.session_state.database["characters"]:
        with st.expander(c.name):
            draw_character(c)

    with st.expander("Create New Character"):
        with st.form("character_create"):
            name = st.text_input("Name")
            likes = st.multiselect("Likes", st.session_state.database["likes"])
            dislikes = st.multiselect("Dislikes",st.session_state.database["dislikes"])
            personality = st.selectbox("Personality",st.session_state.database["personality"])
    
            if st.form_submit_button():
                character = Character(name=name, likes=likes, dislikes=dislikes,personality=personality)
                st.session_state.database["characters"].append(character)

def draw_resource(resource):
    st.write(resource)


def draw_material(material):
    st.subheader(material.name)
    st.info(material.description)
    for k,v in material.data.items():
        st.write(f"__{k.replace('_',' ').title()}__")
        st.write(v)



def draw_resource_library():
    st.subheader("Resource Library")

    for c in st.session_state.database["resources"]:
        with st.expander(c.name):
            draw_resource(c)

    with st.expander("Create New Resource"):
        with st.form("resource_create"):
            yaml = st.text_area("Resource YAML")

            if st.form_submit_button():
                resource = Resource.parse_raw(yaml)
                st.session_state.database["resources"].append(resource)




def draw_material_library():
    st.subheader("Material Library")

    for c in st.session_state.database["materials"]:
        with st.expander(c.name):
            draw_material(c)

def page_database():
    st.header("User Settings")

    draw_character_library()

    draw_resource_library()        

    draw_material_library()



def page_generate_story():

    title_space = st.container()

    with st.expander("Story Board"):

        with st.form("story"):
            NAME = st.text_input("Character Name","Emmy")
            CHARACTER = st.selectbox("Character",characters)
            DISLIKES = st.selectbox("Dislikes", dislikes)
            DESTINATION = st.selectbox("Destination",destination)

            TEXT_STYLE = st.selectbox("Language Style", ["simple", "very simple", "primary school"])
            LANGUAGE = st.selectbox("Language", ["English", "French"])
            TENSE = st.selectbox("Tense",tense)

            s_likes = st.multiselect("Likes", likes)
            LIKES = ", ".join(s_likes)

            if st.form_submit_button():
                story_data = {"content":{}, "meta_data":{}}
                
                full_prompt = story_prompt.format(**locals())
                
                # Create an on the fly message stack
                messages = [{"role": "system", "content": st.session_state.primer}]
                messages.extend([{"role": "user", "content": full_prompt}])
                r = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
                # extract the data
                story = r["choices"][0]["message"]["content"]
                st.write(story)

                # generate title
                messages = [
                    {"role": "system", "content": st.session_state.primer},
                    {"role": "assistant", "content": story},
                    {"role": "user", "content": title_prompt}
                    ]
            
                r = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
                title = r["choices"][0]["message"]["content"]
                with title_space:
                    st.write(title)


                # generate questions
                messages = [
                    {"role": "system", "content": st.session_state.primer},
                    {"role": "assistant", "content": story},
                    {"role": "user", "content": question_prompt}
                    ]
            
                r = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
                question = r["choices"][0]["message"]["content"]
                st.write(question)

                # generate flashcards
                messages = [
                    {"role": "system", "content": st.session_state.primer},
                    {"role": "assistant", "content": story},
                    {"role": "user", "content": flashcard_prompt}
                    ]
            
                r = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
                flashcards = r["choices"][0]["message"]["content"]
                st.write(flashcards)


                content = {
                    "title":title,
                    "story":story,
                    "flashcards":flashcards,
                    "questions":question
                }


                story_data["content"] = content

                st.session_state.story_data = story_data

                PROMPT = image_prompt.format(**locals())

                response = openai.Image.create(

                    prompt=PROMPT,

                    n=1,

                    size="256x256",

                )
                story_data["image"] = response["data"][0]['url']


    st.header(st.session_state.story_data.get("content",{}).get("title",""))
    st.markdown(f"![Alt Text]({st.session_state.story_data.get('image')})")
    st.write(st.session_state.story_data.get("content",{}).get("story",""))
    st.write(st.session_state.story_data.get("content",{}).get("flashcards",""))
    st.write(st.session_state.story_data.get("content",{}).get("questions",""))
    
    