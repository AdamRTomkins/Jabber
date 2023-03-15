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
