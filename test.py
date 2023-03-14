from models import *
from resources import CHARACTERS

from core_utils import *


# Workspaces
# Create a basic workspace to store the available characters
workspace = Workspace(
    id="123",
    characters=CHARACTERS,
    available_tasks=[],
)

## Steps
ex_yml = """
 version: 1.0.0
 name: Example
 description: An example resource type
 slots:
   characters:
     - CHAR1
     - CHAR2
   properties:
     LOCATION: ["Doctor", "Cafe"]
     LANGUAGE: ["English", "French"]
 import_tasks:
     id: 123456
     name: translate

 tasks:
  - generate_story:
     id: 0
     type: GenerateTask
     prompt: 
        user: "Generate a Story about a child called {CHAR1.name} going to a {LOCATION}"
     required_slots:
       characters : [CHAR1]
       properties : [LOCATION]
  - translate:
     id: 1
     type: GenerateTask
     prompt:
       assistant: "Story: {MEMORY.generate_story}" 
       user: "Please translate the above story into {LANGUAGE}"
     required_slots:
       properties : [LANGUAGE]
     required_outputs:
       - generate_story

  - summary:
     id: 2
     type: GenerateSummary
     required_outputs:
       - generate_story      

  - title:
     id: 2
     type: GenerateTitle
     required_outputs:
       - summary       
"""


# Select a resource
resource = Resource.parse_raw(ex_yml)

# Extract the resource Requirements

# Build a UI to Fulful the resourcw requirements
requirements = fulfil_slots(resource=resource, workspace=workspace)
# Validate that we have the right requirements.

# Generate the Resource
materials = generate_materials(
    workspace=workspace, resource=resource, requirements=requirements
)


for k, v in materials.items():
    print(f">>> {k}", v, sep="/n/n")
