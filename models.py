from pydantic import BaseModel, validator
from pydantic_yaml import YamlModel

from pydantic import root_validator, ValidationError
from pydantic_yaml import VersionedYamlModel
from typing import List, Optional, Dict, Union, Literal, Any

import streamlit as st

import openai
import re


class Material(BaseModel):
    id: str
    name: str
    description: str
    resource_id: str
    data: Dict[str, Any]


class Character(BaseModel):
    name: str
    likes: List[str]
    dislikes: List[str]
    gender: str = "girl"
    hair_colour: str = "red"
    eye_colour: str = "blue"
    wearing: str = "a yellow dress"
    lives_in: str = "the woods"
    flair: str = "an umbrella"
    personality: str


class ResourceRequirements(BaseModel):
    characters: Dict[str, Character]
    properties: Dict[str, str]


class Slots(BaseModel):
    characters: Optional[List[str]]
    properties: Optional[Dict[str, List[str]]]


class TaskParams(YamlModel):
    id: str
    type = "Base"
    _TaskParams: str = "TaskParams"
    keep_output: bool = True  # ensure the final memory trace is returned
    required_slots: Dict = (
        {}
    )  # The variables that this Task needs direct access to for the prompt formatting (prompt infils)
    required_outputs: List[str] = []  # Required Computed Items to be stored in memory

    class Config:
        arbitrary_types_allowed = True
        allow_reuse = True
        extra = "forbid"

    def execute(self, requirements: ResourceRequirements, memory: Dict):
        return self.id


# TODO: How do we allow the user to pass in specific vartiables from their workspace, such as API Keys
class GenerateTextTask(TaskParams):
    type = "GenerativeText"
    GenerativeText: str = "GenerativeText"

    prompt: Dict[str, str]
    primer: str = "You are a friendly assistant."

    def execute(self, requirements: ResourceRequirements, memory: Dict):
        openai.api_key = st.session_state.key

        messages = [{"role": "system", "content": self.primer}]
        for role, content in self.prompt.items():
            messages.extend(
                [
                    {
                        "role": role,
                        "content": resolve_prompt(content, requirements, memory),
                    }
                ]
            )

        r = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        return r["choices"][0]["message"]["content"]


class GenerativeShortSummary(TaskParams):
    type = "GenerativeShortSummary"
    GenerativeShortSummary: str = "GenerativeShortSummary"
    primer: str = "You are a friendly assistant."

    def execute(self, requirements: ResourceRequirements, memory: Dict):
        openai.api_key = st.session_state.key

        messages = [{"role": "system", "content": self.primer}]

        for memory_content in self.required_outputs:
            messages.extend(
                [{"role": "assistant", "content": memory.get(memory_content)[-1]}]
            )

        messages.extend(
            [
                {
                    "role": "user",
                    "content": "Summarise the above Content with a short text of a few simple sentences.",
                }
            ]
        )

        r = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        return r["choices"][0]["message"]["content"]


class GenerativeTitle(TaskParams):
    type = "GenerativeTitle"
    GenerativeTitle: str = "GenerativeTitle"

    primer: str = "You are are a story editor who writes short and snappy titles to interesting stories that would sell well."

    def execute(self, requirements: ResourceRequirements, memory: Dict):
        openai.api_key = st.session_state.key

        messages = [{"role": "system", "content": self.primer}]

        for memory_content in self.required_outputs:
            messages.extend(
                [{"role": "assistant", "content": memory.get(memory_content)[-1]}]
            )

        messages.extend(
            [
                {
                    "role": "user",
                    "content": "Write a simple, one sentence Book Title for the Story above.",
                }
            ]
        )

        r = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        return r["choices"][0]["message"]["content"]


class GenerateImage(TaskParams):
    type = "GenerativeImage"
    GenerateImage: str = "GenerateImage"
    image_prompt: str

    def execute(self, requirements: ResourceRequirements, memory: Dict):
        response = openai.Image.create(
            prompt=resolve_prompt(self.image_prompt, requirements, memory),
            n=1,
            size="256x256",
        )
        return response["data"][0]["url"]


class GenerateCharacterImage(TaskParams):
    type = "GenerativeCharacterImage"
    GenerateCharacterImage: str = "GenerateCharacterImage"
    character_image_prompt: str = "A simple watercolour portrait of a {CHAR1.gender} called {CHAR1.name} with {CHAR1.hair_colour} hair, and {CHAR1.eye_colour} eyes, wearing a {CHAR1.wearing}, holding a {CHAR1.flair}, who lives in {CHAR1.lives_in}"

    def execute(self, requirements: ResourceRequirements, memory: Dict):
        response = openai.Image.create(
            prompt=resolve_prompt(self.character_image_prompt, requirements, memory),
            n=1,
            size="256x256",
        )
        return response["data"][0]["url"]


class LoadTask(TaskParams):
    type = "LoadTask"
    preload_id: str


class UserPromptTask(TaskParams):
    type = "UserPrompt"
    user_prompt: str


class Resource(VersionedYamlModel):
    """Model with a maximum version set."""

    name: str
    description: str = ""
    tags: List[str] = []
    slots: Slots = Slots()
    import_tasks: Optional[Dict[str, str]]
    tasks: List[
        Dict[
            str,
            Union[
                GenerateCharacterImage,
                LoadTask,
                UserPromptTask,
                GenerativeShortSummary,
                GenerativeTitle,
                GenerateImage,
                GenerateTextTask,
            ],
        ]
    ]  # I Really, Really don't like this, but with semantic versioning, we can do little bumps and be happy

    class Config:
        min_version = "0.0.1"

    @root_validator
    def check_slots_and_memory(cls, values):
        tasks, slots = values.get("tasks"), values.get("slots")

        # Track the order of the tasks and the memory that is being written to.
        memory_slots = []

        for task in tasks:
            for task_name, task_params in task.items():
                # Assert each required slot value is present in the specific slot types
                for slot_type, slot_values in task_params.required_slots.items():
                    for slot_value in slot_values:
                        try:
                            assert slot_value in getattr(slots, slot_type)
                        except:
                            raise ValueError(
                                f"Required Slot Value {slot_value} is not in the current assigned slot {slot_type} for the resource. Perhaps add {slot_value} to slots.{slot_type}, for example: {list(getattr(slots,slot_type).keys())+[slot_value]}"
                            )

                # Validate that any set variables that are depended upon have already been set
                for output in task_params.required_outputs:
                    try:
                        assert output in memory_slots
                    except:
                        raise ValidationError(
                            f"Required Output {output} is not in the current Memory Slots({memory_slots}"
                        )

                # Validate we don't overwrite memory

                try:
                    assert task_name not in memory_slots
                except:
                    raise ValidationError(
                        f"Task Name {task_name} is already in a memory slot. Please rename this task."
                    )
                memory_slots.append(task_name)

        return values


class Workspace(BaseModel):
    id: str
    characters: List[Character] = []
    available_tasks: List[TaskParams]


def resolve_prompt(prompt: str, requirements: ResourceRequirements, memory: Dict):
    """Resolve the Prompt Variables, replacing properties, characters and Memory call backs.

    TODO: Improve and standardise how we separate characters and memory and properties
    """

    # Extract everything between {}
    # split them by .
    res = re.findall(r"\{.*?\}", prompt)
    replacements = {}

    for r in res:
        text = r[1:-1]
        features = text.split(".")

        # For all the single ones, pull them out of properties
        if len(features) == 1:
            replacements[r] = requirements.properties.get(features[0])

        # For the len twos:
        # pull the first and getattr on the second.
        # Characters
        if len(features) == 2:
            # Resolve Memory Lookup
            if features[0] == "MEMORY":
                assert len(memory[features[1]]) > 0
                replacements[r] = memory[features[1]][-1]
            # TODO: Improve Character Signification to not just be the default if its not memory
            else:
                # Resolve Character Lookup
                character = requirements.characters.get(features[0])
                replacements[r] = getattr(character, features[1])

        for k, v in replacements.items():
            if type(v) is List:
                if len(v) == 1:
                    v = v[0]
                v = ", ".join(v[:-2]) + " and " + v[-1]
            prompt = prompt.replace(k, v)

    return prompt
