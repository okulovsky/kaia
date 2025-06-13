from dataclasses import dataclass
from .scene import Scene
from .prompter_helpers import *
from .scene import Medium


@dataclass
class FullPrompt:
    task_name: str
    prompt: str
    system_prompt: str|None = None
    temperature: float|None = None

class Prompter:
    def __init__(self, system_prompt: str, dialog_temperature: float):
        self.dialog_temperature = dialog_temperature
        self.system_prompt = system_prompt


    def _make(self, *parts) -> str:
        return '\n\n'.join(parts)

    def _summary(self, target = 'dialog', length = 100) -> str:
        return f"Summarize the {target} in one paragraph, no longer than {length} words. Pay attention to the actual progression of the events and the characters development. Also pay attention for details that could be important in continuation of the story."

    def next_messages(self, scene: Scene) -> FullPrompt:
        prompt = self._make(
            "== Introduction ==",
            build_introduction(scene),
            "== Current scene ==",
            build_current_scene(scene),
            "== The task ==",
            build_next_message_task(scene)
        )
        return FullPrompt('next', prompt, self.system_prompt, self.dialog_temperature)

    def intermediate_summary(self, scene: Scene) -> FullPrompt:
        prompt = self._make(
            "== Introduction ==",
            build_introduction(scene),
            "== Current scene ==",
            build_current_scene(scene, False),
            "== The task ==",
            self._summary("dialog")
        )
        return FullPrompt("intermediate_summary", prompt, self.system_prompt)

    def scene_summary(self, scene: Scene) -> FullPrompt:
        prompt = self._make(
            "== Introduction ==",
            build_introduction(scene),
            "== Current scene ==",
            build_current_scene(scene, False),
            "== The task ==",
            self._summary("scene")
        )
        return FullPrompt("scene_summary", prompt, self.system_prompt)

    def cumulative_summary(self, scene: Scene, last_summary) -> FullPrompt:
        prompt = [
            "== Introduction ==",
            build_introduction(scene),
            "== Scenes =="
        ]
        prompt.extend(scene.context.previous_summaries)
        prompt.append(last_summary)
        prompt.append("== Task ==")
        prompt.append(self._summary("story"))
        return FullPrompt("cumulative_summary", self._make(*prompt), self.system_prompt)



    def goal_check(self, scene: Scene) -> FullPrompt:
        prompt = self._make(
            "== Introduction ==",
            build_introduction(scene),
            "== Current scene ==",
            build_current_scene(scene, False),
            "== The task ==",
            f'Consider the following state: {scene.progress.goal}.',
            f"Have it happened in the dialog? It can be written directly or strongly implied.  Answer YES or NO. After this, provide a short explanation no longer than 10 words of why you think so."
        )
        return FullPrompt("goal", prompt, self.system_prompt)




