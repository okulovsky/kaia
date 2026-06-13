from pathlib import Path
from chara.common.tools.llm import PromptTaskBuilder

def setup_default_prompter(prompter: PromptTaskBuilder):
    prompter.set_prompt(Path(__file__).parent/'template.jinja')

