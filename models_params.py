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
