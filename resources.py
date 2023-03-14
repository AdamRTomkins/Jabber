from models import Character, Resource

### Characters
#
adam = Character(
    name="adam",
    likes=["Cats", "Dogs", "Pies"],
    dislikes=["Chocolate", "Bedtime"],
    personality="Shy",
    gender="boy",
    hair_colour="red",
    eye_colour="blue",
    wearing="a plaid shirt",
    lives_in="the beach",
    flair="a hammer",
)

nelly = Character(
    name="nelly",
    likes=["Cats", "Chocolate"],
    dislikes=["Whisky", "Programming"],
    personality="Bold",
    gender="girl",
    hair_colour="dark brown",
    eye_colour="brown",
    wearing="a gray t-shirt",
    lives_in="the woods",
    flair="a black cat",
)

CHARACTERS = [adam, nelly]

## Steps
story = """
 version: 1.0.0
 name: Story and Translation With A Chararacter and a Location
 description: An example resource type
 slots:
   characters:
     - CHAR1
     - CHAR2
   properties:
     LOCATION: ["Doctor", "Cafe"]
     LANGUAGE: ["French", "English"]
 import_tasks:
     id: 123456
     name: translate

 tasks:
  - generate_story:
     id: 0
     type: GenerativeText
     GenerativeText: GenerativeText
     prompt: 
        user: "Generate a Story about a child called {CHAR1.name} with {CHAR2.name} going to a {LOCATION}"
     required_slots:
       characters : [CHAR1, CHAR2]
       properties : [LOCATION]
  - translate:
     id: 1
     type: GenerativeText
     GenerativeText: GenerativeText
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
     GenerativeShortSummary: GenerativeShortSummary
     required_outputs:
       - generate_story      

  - title:
     id: 2
     type: GenerativeTitle
     GenerativeTitle: GenerativeTitle
     required_outputs:
       - summary       
"""

TASKS = []

# Select a resource
RESOURCES = [Resource.parse_raw(story)]
