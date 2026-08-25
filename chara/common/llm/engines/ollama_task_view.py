from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brainbox import BrainBox
from brainbox.deciders import Ollama


@dataclass
class OllamaTaskView:
    """Reads back what `LLMRequest.create_task` put into an Ollama task.

    `create_task` always produces an Ollama task, so an engine that is not BrainBox
    has to introspect it. This is the single place that knows the task layout.
    """

    DECIDER = 'Ollama'
    METHOD = 'question'

    model: str|None
    prompt: str
    system_prompt: str|None
    options: Ollama.Options|None
    image: Path|None

    @staticmethod
    def parse(task: BrainBox.Task) -> OllamaTaskView:
        if task.decider != OllamaTaskView.DECIDER:
            raise ValueError(f"Expected a task for `{OllamaTaskView.DECIDER}`, but the decider is `{task.decider}`")
        if task.method != OllamaTaskView.METHOD:
            raise ValueError(f"Expected the `{OllamaTaskView.METHOD}` method, but it is `{task.method}`")
        arguments = task.arguments
        unexpected = set(arguments) - {'prompt', 'system_prompt', 'options', 'image'}
        if unexpected:
            raise ValueError(f"Unexpected arguments in the task: {sorted(unexpected)}")
        return OllamaTaskView(
            task.optionals.parameter,
            arguments['prompt'],
            arguments.get('system_prompt', None),
            arguments.get('options', None),
            arguments.get('image', None),
        )
