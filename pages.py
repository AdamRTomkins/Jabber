import streamlit as st
from io import StringIO
import json
import openai
import pandas as pd
from pydantic import ValidationError

from data import (
    characters,
    hobbies,
    likes,
    dislikes,
    destination,
    adults,
    tense,
    FIELDS,
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
    resources = {r.name: r for r in st.session_state.database["resources"]}

    resource_name = st.selectbox("Resource Name", resources.keys())
    resource = resources[resource_name]
    st.write(resource.description)
    with st.expander("Resource Config"):
        st.text(resource.yaml())

    # 2. Extract the requirements
    # 3. Filfil the requirements
    mat_name = st.text_input("Material Name", resource.name)
    mat_description = st.text_input("Material Description", resource.description)
    requirements = extract_requirements(resource)

    if st.button("Generate"):
        # 4. Execute the resource
        workspace = Workspace(
            id="1",
            characters=st.session_state.database["characters"],
            available_tasks=[],
        )
        with st.spinner("Generating Material"):
            materials = generate_materials(
                workspace=workspace,
                resource=resource,
                requirements=requirements,
                name=mat_name,
                description=mat_description,
            )

        draw_material(materials)

        # 5. Save the Resource
        st.session_state.database["materials"].append(materials)


def draw_character(character):
    for k, v in character.dict().items():
        st.write(f"__{k}__ :  _{v}_")


def draw_character_library():
    st.subheader("Characters")
    st.info(
        "A place to define and keep your Characters that can be used with any resource."
    )

    for c in st.session_state.database["characters"]:
        with st.expander(c.name):
            draw_character(c)

    with st.expander("Create New Character"):
        with st.form("character_create"):
            name = st.text_input("Name")
            likes = st.multiselect("Likes", st.session_state.database["likes"])
            dislikes = st.multiselect("Dislikes", st.session_state.database["dislikes"])
            personality = st.selectbox(
                "Personality", st.session_state.database["personality"]
            )

            if st.form_submit_button():
                character = Character(
                    name=name, likes=likes, dislikes=dislikes, personality=personality
                )
                st.session_state.database["characters"].append(character)


def draw_resource(resource):
    st.info(resource.description)

    st.code(resource.yaml())


from typing import Dict


def material_mapper(section: Dict):
    funcs = {"image_url": st.image, "text": st.write}

    for k, v in section.items():
        funcs.get(k, st.write)(v)


def draw_material(material):
    st.subheader(material.name)
    st.info(material.description)
    for k, v in material.data.items():
        st.write(f"__{k.replace('_',' ').title()}__")
        material_mapper(v[-1])


def draw_resource_library():
    st.subheader("Resource Library")

    container = st.container()

    with st.expander("Create New Resource"):
        with st.form("resource_create"):
            yaml = st.text_area("Resource YAML")

            if st.form_submit_button():
                try:
                    resource = Resource.parse_raw(yaml)
                    st.session_state.database["resources"].append(resource)
                except ValidationError as e:
                    st.info(
                        "Unable to parse the YAML file, please make sure it is valid with the [YAML Linter](https://www.yamllint.com/) "
                    )
                    st.error(e)
    with container:
        for c in st.session_state.database["resources"]:
            with st.expander(c.name):
                draw_resource(c)


def draw_material_library():
    st.subheader("Material Library")

    deleted = []
    for i, c in enumerate(st.session_state.database["materials"]):
        c1, c2 = st.columns([10, 2])
        with c2:
            if st.button("Delete"):
                deleted.append(i)

        with c1:
            with st.expander(c.name):
                if i in deleted:
                    st.info("This Material has been removed")
                draw_material(c)

    st.session_state.database["materials"] = [
        m
        for i, m in enumerate(st.session_state.database["materials"])
        if i not in deleted
    ]


def page_database():
    st.header("User Settings")

    draw_character_library()

    draw_resource_library()

    draw_material_library()


def page_generate_story():
    title_space = st.container()

    with st.expander("Story Board"):
        with st.form("story"):
            NAME = st.text_input("Character Name", "Emmy")
            CHARACTER = st.selectbox("Character", characters)
            DISLIKES = st.selectbox("Dislikes", dislikes)
            DESTINATION = st.selectbox("Destination", destination)

            TEXT_STYLE = st.selectbox(
                "Language Style", ["simple", "very simple", "primary school"]
            )
            LANGUAGE = st.selectbox("Language", ["English", "French"])
            TENSE = st.selectbox("Tense", tense)

            s_likes = st.multiselect("Likes", likes)
            LIKES = ", ".join(s_likes)

            if st.form_submit_button():
                story_data = {"content": {}, "meta_data": {}}

                full_prompt = story_prompt.format(**locals())

                # Create an on the fly message stack
                messages = [{"role": "system", "content": st.session_state.primer}]
                messages.extend([{"role": "user", "content": full_prompt}])
                r = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages
                )
                # extract the data
                story = r["choices"][0]["message"]["content"]
                st.write(story)

                # generate title
                messages = [
                    {"role": "system", "content": st.session_state.primer},
                    {"role": "assistant", "content": story},
                    {"role": "user", "content": title_prompt},
                ]

                r = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages
                )
                title = r["choices"][0]["message"]["content"]
                with title_space:
                    st.write(title)

                # generate questions
                messages = [
                    {"role": "system", "content": st.session_state.primer},
                    {"role": "assistant", "content": story},
                    {"role": "user", "content": question_prompt},
                ]

                r = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages
                )
                question = r["choices"][0]["message"]["content"]
                st.write(question)

                # generate flashcards
                messages = [
                    {"role": "system", "content": st.session_state.primer},
                    {"role": "assistant", "content": story},
                    {"role": "user", "content": flashcard_prompt},
                ]

                r = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=messages
                )
                flashcards = r["choices"][0]["message"]["content"]
                st.write(flashcards)

                content = {
                    "title": title,
                    "story": story,
                    "flashcards": flashcards,
                    "questions": question,
                }

                story_data["content"] = content

                st.session_state.story_data = story_data

                PROMPT = image_prompt.format(**locals())

                response = openai.Image.create(
                    prompt=PROMPT,
                    n=1,
                    size="256x256",
                )
                story_data["image"] = response["data"][0]["url"]

    st.header(st.session_state.story_data.get("content", {}).get("title", ""))
    st.markdown(f"![Alt Text]({st.session_state.story_data.get('image')})")
    st.write(st.session_state.story_data.get("content", {}).get("story", ""))
    st.write(st.session_state.story_data.get("content", {}).get("flashcards", ""))
    st.write(st.session_state.story_data.get("content", {}).get("questions", ""))


from streamlit_tags import st_tags


def page_create_resource():
    st.subheader("Details")

    name = st.text_input("Name", "Your Resource Name")
    description = st.text_input("Name", "Your Resource Description")

    st.subheader("Properties")

    num_characters = st.number_input(
        "Number of Characters", min_value=0, max_value=4, value=0, step=1
    )

    properties = st_tags(
        label="Properties:",
        text="Press enter to add more",
        value=[],
        suggestions=["LOCATION", "MOOD", "TENSE"],
        maxtags=15,
        key="1",
    )

    props = {}
    c1, c2 = st.columns([1, 10])
    with c2:
        for prop in properties:
            props[prop] = st_tags(
                label=prop,
                text="Press enter to add more",
                value=FIELDS.get(prop, []),
                suggestions=FIELDS.get(prop, []),
                maxtags=15,
                key=prop,
            )

    from models import Slots

    slots = Slots(
        characters=[f"CHAR{i+1}" for i in range(num_characters)], properties=props
    )

    task_show = st.container()

    from models import (
        GenerateTextTask,
        GenerativeShortSummary,
        GenerativeTitle,
        GenerateImage,
        GenerateCharacterImage,
    )
    import typing

    task_params = {
        "Generate Text": GenerateTextTask,
        "Generate Summary": GenerativeShortSummary,
        "Generate Title": GenerativeTitle,
        "Generate Image": GenerateImage,
        "Generate Character Image": GenerateCharacterImage,
    }

    with st.expander("Add new Task"):
        task_type = st.selectbox("Task Type", task_params.keys())
        task_class = task_params[task_type]
        hints = typing.get_type_hints(task_class)
        c1, c2 = st.columns([1, 10])

        with c2:
            with st.form("Add Task"):
                params = {}

                task_name = st.text_input("Task Name")

                params["keep_output"] = st.checkbox("Keep the Output", True)
                required_characters = st.multiselect(
                    "Required Characters", slots.characters
                )
                required_parameters = st.multiselect(
                    "Required Parameters", slots.properties.keys()
                )
                params["required_slots"] = {
                    "characters": required_characters,
                    "properties": required_parameters,
                }
                params["required_outputs"] = st.multiselect(
                    "Required Memory Slots",
                    sum([list(t.keys()) for t in st.session_state.tasks], []),
                )
                params["id"] = "123"

                for k, v in task_class.__fields__.items():
                    if (
                        k not in params and k != "type" and k[0] != k[0].upper()
                    ):  # hack to hide Generative
                        n = k.title()
                        if getattr(v, "required"):
                            n = n + "*"

                        if hints[k] is str:
                            params[k] = st.text_input(n, getattr(v, "default"))
                        elif hints[k] is typing.Dict[str, str]:
                            prompts = st.text_area(
                                n,
                                """assistant:Story:{MEMORY.task_name}
    user:Create a story about {CHAR.name} in {LOCATION} (For Example)""",
                            )

                            # Constrict this better
                            params[k] = {
                                r.split(":")[0].strip(): r.split(":")[1].strip()
                                for r in prompts.split("\n")
                            }
                        else:
                            st.error("Cant build a UI for this yet:")
                            st.write(n)
                            st.write(v)
                            st.write(getattr(v, "required"))
                            st.write(hints.get(k))

                if st.form_submit_button("Add Task"):
                    st.session_state.tasks.append(
                        {task_name: task_params[task_type](**params)}
                    )
                    task_name = ""
                    task_description = ""

    with task_show:
        st.subheader(f"Tasks ({len(st.session_state.tasks)})")
        if st.button("Clear Tasks"):
            st.session_state.tasks = []
        for task in st.session_state.tasks:
            with st.expander(list(task.keys())[0]):
                for k, v in task.items():
                    st.write(f"__{k}__ ({type(v)})")
                    st.code(v.yaml())

    r = Resource(
        version="0.0.1",
        name=name,
        description=description,
        slots=slots,
        tasks=st.session_state.tasks,
    )

    with st.expander("View Config"):
        st.text(r.yaml())

    if st.button("Add To Resources"):
        r = Resource(
            version="0.0.1",
            name=name,
            description=description,
            slots=slots,
            tasks=st.session_state.tasks,
        )

        try:
            st.session_state.database["resources"].append(r)
            st.success(f"Added {r.name} to the Resource Library")
            st.session_state.tasks = []
        except ValidationError as e:
            st.info(
                "Unable to parse the YAML file, please make sure it is valid with the [YAML Linter](https://www.yamllint.com/) "
            )
            st.error(e)
