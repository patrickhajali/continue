
import difflib
import re
from textwrap import dedent
from continuedev.libs.util.strings import remove_quotes_and_escapes
from continuedev.models.filesystem import RangeInFile, RangeInFileWithContents
from ...core.main import ChatMessage, Step
from ...core.observation import Observation
from ...libs.llm.base import LLM, PromptTemplate
from typing import Coroutine, List, Optional, Union, Any, AsyncGenerator, Callable
from ...core.sdk import ContinueSDK, Models


 
class EditPlusStep(Step): 
    
    user_input: str
    model: Optional[LLM] = None
    name: str = "Editing Code"
    hide = False
    description: str = ""
    _prompt: str = ""
    _previous_contents: str = ""
    _new_contents: str = ""
    _prompt_and_completion: str = ""
    summary_prompt: str = "Please briefly explain the changes made to the code above. Give no more than 2-3 sentences, and use markdown bullet points:"


    _prompt = dedent("""
        I am providing a snippet of code with line numbers (marked as comments) included for reference.
        The line numbers are not part of the actual code and should be disregarded in any edits or execution.
        {file_content}
        
        Your task is to edit the code to satisfy the following: {user_input}
                     
        Output the changes as a diff patch and only include the changes themselves.
        You can only reference the change command 'c'. No other actions are allowed. 
        Do not output any other text. Make sure to maintain the correct amount of whitespace.
        Here is a very simple example of how you should format your output:
        
        # Begin Example Output
        4c4
        <       return get_length(lst) % 2 == 0
        ---
        >       return len(lst) % 2 == 0
        # End Example Output""")
        
        

    async def describe(self, models: Models) -> Coroutine[str, None, None]:
        name = await models.summarize.complete(
            f"Write a very short title to describe this requested change (no quotes): '{self.user_input}'. This is the title:"
        )
        self.name = remove_quotes_and_escapes(name)

        if self._previous_contents.strip() == self._new_contents.strip():
            return "No edits were made"
        else:
            return None
        
    async def run(self, sdk: ContinueSDK) -> Coroutine[Observation, None, None]:
        
        # rifs for all active contexts
        range_in_files = sdk.get_code_context(only_editing=True)

        # If nothing highlighted, insert at the cursor if possible
        if len(range_in_files) == 0:
            highlighted_code = await sdk.ide.getHighlightedCode()
            if highlighted_code is not None:
                for rif in highlighted_code:
                    if rif.range.start == rif.range.end:
                        range_in_files.append(
                            RangeInFileWithContents.from_range_in_file(rif, "")
                        )

        # # If all of the ranges are point ranges, only edit the last one
        # if all([rif.range.start == rif.range.end for rif in range_in_files]):
        #     range_in_files = [range_in_files[-1]]

        
        # ----------------- Loading File Contents ----------------------------
        await sdk.update_ui()

        # Only considering first rif
        file_path = range_in_files[0].filepath
        file_content = await sdk.ide.readFile(file_path)
        # messages = await sdk.get_chat_context()
        # messages.append(ChatMessage(
        #     role="user",
        #     content=self._prompt.format(
        #         user_input=self.user_input, file_content=file_content),
        #     summary=""
        # ))

        # Add line numbers to file contents
        file_lines = file_content.split("\n")
        numbered_lines = [(line + "  # line {}".format(index + 1)) if line.strip() != '' else line
                      for index, line in enumerate(file_lines)]
        numbered_file_content = "\n".join(numbered_lines)

        messages = [ChatMessage(
            role="user",
            content=self._prompt.format(
                user_input=self.user_input, file_content=numbered_file_content),
            summary=""
        )]

        # -----------------  ----------------------------
        # Create a copy of filelines 
        new_lines = file_lines.copy()
        
        model_out_lines = []
        action_line_number = 0
        async for line in iterate_by_line(sdk.models.default.stream_chat(messages), lambda m: m["content"], sdk.current_step_was_deleted):
            
            model_out_lines.append(line)
            
            # Try with change 'c' only first (see prompt), then add 'a' and 'd'

            # Check for numbers 
            if re.match(r'^(\d+)', line):
                nums = line.split('c')
                # only one action line num since we are only allowing change for now
                # (i.e. always refering to the same index in both old and new doc)
                action_line_number = int(nums[0]) 
            
            elif line.startswith('<'):
                # Part of a change or delete action.
                pass

            elif line.startswith('>'):
                try:  
                    new_lines[action_line_number - 1] = line[2:]
                except: 
                    pass
            else: 
                pass

            new_file_contents = ("\n".join(new_lines))

            step_index = sdk.history.current_index

            await sdk.ide.showDiff(file_path, new_file_contents, step_index)
        
        # ----------------- Generating Summary and Updating Context ----------------------------

        # changes = "\n".join(
        #     difflib.ndiff(
        #         self._previous_contents.splitlines(),
        #         self._new_contents.splitlines(),
        #     )
        # )

        # if sdk.config.disable_summaries:
        #     self.name = ""
        #     self.description = f"Edited {len(self.range_in_files)} files"
        #     await sdk.update_ui()
        # else:
        #     self.name = "Generating summary"
        #     self.description = ""
        #     async for chunk in sdk.models.summarize.stream_complete(
        #         dedent(
        #             f"""\
        #     Diff summary: "{self.user_input}"

        #     ```diff
        #     {changes}
        #     ```

        #     {self.summary_prompt}"""
        #         )
        #     ):
        #         self.description += chunk
        #         await sdk.update_ui()

        # sdk.context.set("last_edit_user_input", self.user_input)
        # sdk.context.set("last_edit_diff", changes)
        # sdk.context.set("last_edit_range", self.range_in_files[-1].range)
         



# Create async function to apply edits from patch to original file
async def iterate_by_line(generator: AsyncGenerator[str, None], get_content: Callable[[Any], str], should_cancel: Callable[[], bool]) -> AsyncGenerator[str, None]:
        
        """Converts an async generator of chunks into an async generator of lines."""

        unfinished_line = ""
        async for chunk in generator:
            if should_cancel():
                return
            try: 
                chunk_content = get_content(chunk)
                chunk_lines = chunk_content.split("\n")
                chunk_lines[0] = unfinished_line + chunk_lines[0]
                if chunk_content.endswith("\n"):
                    unfinished_line = ""
                    chunk_lines.pop()  # because this will be an empty string
                else:
                    unfinished_line = chunk_lines.pop()

                for line in chunk_lines:
                    yield line
            except: 
                pass

        if unfinished_line != "" and unfinished_line != "\n":
            yield unfinished_line




    