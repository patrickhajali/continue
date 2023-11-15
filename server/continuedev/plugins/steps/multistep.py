from textwrap import dedent

from continuedev.plugins.steps.chat import SimpleChatStep
from continuedev.core.main import ChatMessage, Step

from ..steps.codebase import AnswerQuestionChroma, RetrieveCodebaseContext



class PlanStep(Step): 

    user_input: str
    _prompt : str = dedent("""
    You are given the following instructions: "{user_input}".
            
    Create a plan for how you will complete the task.

    Your plan will include:
    1. A high-level description of how you are going to accomplish the task
    2. A list of which files you will edit and a description of what you will change in each file
    3. A description of code in the current codebase that would be useful to reference/use
                           
    Format your plan as a markdown list, with each item in the list being a file you will edit.
    """)

    async def run(self, sdk):

        messages = [
            ChatMessage(
                        role="user",
                        content=self._prompt.format(user_input=self.user_input),
                        summary=self.user_input,
                    )
        ]

        await sdk.run_step(
            SimpleChatStep(
                name="Planning",
                description=f"Planning...",
                messages=messages
            )
        ) 


class VanillaMultiStepStep(Step):
    user_input: str

    async def run(self, sdk):

        # 1. Gennerate plan given task desc
        await sdk.run_step(PlanStep(user_input=self.user_input))

        messages = await sdk.get_chat_context()

        # 2. Pull relevant code
        await sdk.run_step(RetrieveCodebaseContext(user_input=messages[-1].content))

        # messages = await sdk.get_chat_context()





