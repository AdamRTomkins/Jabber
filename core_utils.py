from models import *
import re


def fulfil_slots(resource: Resource, workspace: Workspace):
    # This is a dummy way to fill slots
    characters = {
        c: workspace.characters[i] for i, c in enumerate(resource.slots.characters)
    }

    # Lets just grab the first property
    properties = {p: v[1] for p, v in resource.slots.properties.items()}

    return ResourceRequirements(characters=characters, properties=properties)


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
            print(k, v, memory.keys())
            prompt = prompt.replace(k, v)
    return prompt


from collections import defaultdict


def generate_materials(
    workspace: Workspace,
    resource: Resource,
    requirements: ResourceRequirements,
    name="Resource",
    description="description",
):
    """Execute the Resource one task at a time"""

    # Create a new session of memory per material generation
    memory = defaultdict(list)
    keep_flag = {}
    # Cycle through the tasks and execute them, storing the result in memory
    for task in resource.tasks:
        memory = execute_task(task, memory, requirements)
        keep_flag[list(task.keys())[0]] = list(task.values())[0].keep_output

    data = {k: v for k, v in memory.items() if keep_flag[k]}
    material = Material(
        id="id",
        name=name,
        description=description,
        resource_id=resource.name,
        data=data,
    )

    return material


def execute_task(task: Dict, memory: Dict, requirements: ResourceRequirements):
    """Execute a task given the memory trace and the resource requirements"""
    # This is a single dict which is not good.
    # This doesn't need to be a loop as there is only one. If this could be a tuple that would be better

    for task_name, task_data in task.items():
        memory[task_name].append(task_data.execute(requirements, memory))

    return memory
