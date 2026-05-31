from pathlib import Path
from chara.common.tools.llm import PromptTaskBuilder

def setup_default_prompter(prompter: PromptTaskBuilder):
    prompter.read_default_prompt(Path(__file__).parent/'template.jinja')

