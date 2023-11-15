
# Step which feeds the SDK to the LLM along with high-level task desciption and description of how to make a step, 
# and then prompts the LLM to generate a step. 

from continuedev.core.main import Step


class GenerateStep(Step):
    user_input : str