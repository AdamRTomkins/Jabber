from models import Character, Resource

### Characters
#
adam = Character(
    name="adam",
    likes=["Cats", "Dogs","Pies"],
    dislikes=["Chocolate", "Bedtime"],
    personality="Shy",
)

nelly = Character(
    name="nelly",
    likes=["Cats", "Chocolate"],
    dislikes=["Whisky", "Programming"],
    personality="Bold"
)

CHARACTERS = [adam,nelly]

## Steps
ex_yml = """
 version: 1.0.0
 name: Story and Translation With A Chararacter and a Location
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
        user: "Generate a Story about a child called {CHAR1.name} with {CHAR1.name} going to a {LOCATION}"
     required_slots:
       characters : [CHAR1, CHAR2]
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




TASKS = []


# Select a resource
RESOURCES = [Resource.parse_raw(ex_yml)]