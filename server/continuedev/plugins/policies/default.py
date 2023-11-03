from typing import Type, Union

from ..steps.chroma import AnswerQuestionChroma

from ...core.config import ContinueConfig
from ...core.main import History, Policy, Step
from ...core.observation import UserInputObservation
from ... core.steps import WaitForUserInputStep
from ...plugins.steps.inline_edits import EditPlusStep
from ..steps.chat import SimpleChatStep
from ..steps.custom_command import CustomCommandStep
from ..steps.main import EditHighlightedCodeStep, FasterEditHighlightedCodeStep
from ..steps.steps_on_startup import StepsOnStartupStep


# When importing with importlib from config.py, the classes do not pass isinstance checks.
# Mapping them here is a workaround.
# Original description of the problem: https://github.com/continuedev/continue/pull/581#issuecomment-1778138841
REPLACEMENT_SLASH_COMMAND_STEPS = [AnswerQuestionChroma]


def parse_slash_command(inp: str, config: ContinueConfig) -> Union[None, Step]:
    """
    Parses a slash command, returning the command name and the rest of the input.
    """
    if inp.startswith("/"):
        command_name = inp.split(" ")[0].strip()
        after_command = " ".join(inp.split(" ")[1:])

        for slash_command in config.slash_commands:
            if slash_command.name == command_name[1:]:
                params = slash_command.params
                params["user_input"] = after_command
                try:
                    for replacement_step in REPLACEMENT_SLASH_COMMAND_STEPS:
                        if slash_command.step.__name__ == replacement_step.__name__:
                            return replacement_step(**params)

                    return slash_command.step(**params)
                except TypeError as e:
                    raise Exception(
                        f"Incorrect params used for slash command '{command_name}': {e}"
                    )
    return None


def parse_custom_command(inp: str, config: ContinueConfig) -> Union[None, Step]:
    command_name = inp.split(" ")[0].strip()
    after_command = " ".join(inp.split(" ")[1:])
    for custom_cmd in config.custom_commands:
        if custom_cmd.name == command_name[1:]:
            slash_command = parse_slash_command(custom_cmd.prompt, config)
            if slash_command is not None:
                return slash_command
            return CustomCommandStep(
                name=custom_cmd.name,
                description=custom_cmd.description,
                prompt=custom_cmd.prompt,
                user_input=after_command,
                slash_command=command_name,
            )
    return None


## Test 
class DefaultPolicy(Policy):
    default_step: Type[Step] = SimpleChatStep
    default_params: dict = {}

    def next(self, config: ContinueConfig, history: History) -> Step:
        # At the very start, run initial Steps specified in the config
        if history.get_current() is None:
            return StepsOnStartupStep()

        observation = history.get_current().observation
        if observation is not None and isinstance(observation, UserInputObservation):
            # This could be defined with ObservationTypePolicy. Ergonomics not right though.
            user_input = observation.user_input

            slash_command = parse_slash_command(user_input, config)
            if slash_command is not None:
                if (
                    getattr(slash_command, "user_input", None) is None
                    and history.get_current().step.user_input is not None
                ):
                    history.get_current().step.user_input = (
                        history.get_current().step.user_input.split()[0]
                    )
                return slash_command

            custom_command = parse_custom_command(user_input, config)
            if custom_command is not None:
                return custom_command

            if user_input.startswith("/edit"):
                return EditHighlightedCodeStep(user_input=user_input[5:])

            return self.default_step(**self.default_params)

        return None


class MultiStepPolicy(Policy):
    ''' 
    Default policy takes in current observation and runs
    the specified slash command (or custom command) and updates
    the history. If no slash commands are given, it defaults to
    SimpleChatStep. 

    MultiStepPolicy takes in current observation, then:
        - Step1: Propose Code
        - Step2: Review Code and Propose New Code-Snippets
        - Step2.5: Present to User, Who selects to keep or not

    A policy needs to chain steps! What are the key steps? 
        - generate code from high-level NL description 
        - review or validate code 
        - propose new functions 

    Other ideas: 
        - code translation
        - constrain -> build a constrain step 
    '''
    default_step: Type[Step] = SimpleChatStep
    default_params: dict = {}

    def next(self, config: ContinueConfig, history: History) -> Step:
        # At the very start, run initial Steps specified in the config
        if history.get_current() is None:
            return StepsOnStartupStep()

        observation = history.get_current().observation
        # # If there is user input
        if observation is not None and isinstance(observation, UserInputObservation):
            # This could be defined with ObservationTypePolicy. Ergonomics not right though.
            user_input = observation.user_input

            return (
                EditHighlightedCodeStep(user_input=user_input)
                # >> WaitForUserInputStep(prompt = "Continue? (y/n)")
                # >> EditHighlightedCodeStep(user_input="Review the code and propose new code-snippets that can simplify the current implementation.")
            )
        
        # WatforUserInputStep
        # Step 1 - Edit to generate new func: good
        # Step 2 - Review code and propose simplications 
            # Need a way to only edit diff to see what's happening
            # Do this by allowing model to call a function (tool) to insert code here / delete here
        #     slash_command = parse_slash_command(user_input, config)
        #     if slash_command is not None:
        #         if (
        #             getattr(slash_command, "user_input", None) is None
        #             and history.get_current().step.user_input is not None
        #         ):
        #             history.get_current().step.user_input = (
        #                 history.get_current().step.user_input.split()[0]
        #             )
        #         return slash_command

        #     custom_command = parse_custom_command(user_input, config)
        #     if custom_command is not None:
        #         return custom_command

        #     if user_input.startswith("/edit"):
        #         return EditHighlightedCodeStep(user_input=user_input[5:])

        #     return self.default_step(**self.default_params)

        return None
