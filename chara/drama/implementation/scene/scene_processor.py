from dataclasses import dataclass
from .scene import Message, Scene
from brainbox import BrainBox
from brainbox.deciders import Ollama
from .prompter import Prompter, FullPrompt
from abc import ABC, abstractmethod


@dataclass
class SceneProcessorSettings:
    api: BrainBox.Api
    model: str
    max_scene_length: int|None = 30
    debug_prompts_on: tuple[str,...] = ()
    debug_results_on: tuple[str,...] = ()

@dataclass
class SceneProcessorResult:
    next_messages: tuple[Message,...]|None = None
    intermediate_summary: str|None = None
    finished: bool|None = None
    summary: str|None = None
    cumulative_summary: str|None = None

    def get_tags(self):
        result = {k:v for k, v in self.__dict__.items() if k!='next_messages' and v is not None}
        if len(result) == 0:
            return None
        return result

class ISceneProcessor(ABC):
    @abstractmethod
    def process(self, scene: Scene) -> SceneProcessorResult:
        pass



class SceneProcessor(ISceneProcessor):
    def __init__(self, settings: SceneProcessorSettings, prompter: Prompter):
        self.settings = settings
        self.prompter = prompter

    def _exec(self, prompt: FullPrompt):
        print(f'== TASK {prompt.task_name} ==')
        if prompt.task_name in self.settings.debug_prompts_on:
            print('== PROMPT ==')
            print(prompt.prompt)
        result = self.settings.api.execute(
            BrainBox.Task.call(Ollama, self.settings.model).question(
                prompt.prompt,
                prompt.system_prompt,
                None if prompt.temperature is None else dict(temperature=prompt.temperature),
            ))
        if prompt.task_name in self.settings.debug_results_on:
            print('== RESULT ==')
            print(result)
        return result

    def _parse_messages(self, message: str, stop_at_character: str):
        backup_results = []
        results = message.split('\n')
        messages = []
        for r in results:
            r = r.replace('"','')
            try:
                m = Message.parse(r)
                if m.name == stop_at_character:
                    break
                messages.append(Message.parse(r))
            except:
                pass
        if len(messages) > 0:
            return tuple(messages)

        raise ValueError("Cannot generate a parseable message. Attempts were:\n\n"+"\n".join(backup_results))

    def _parse_goal(self, s: str):
        if s.startswith('YES'):
            return True


    def process(self, scene: Scene):
        result = SceneProcessorResult()
        if self.settings.max_scene_length is not None and len(scene.messages)>self.settings.max_scene_length:
            result.intermediate_summary = self._exec(self.prompter.intermediate_summary(scene))
        raw_messages = self._exec(self.prompter.next_messages(scene))
        result.next_messages = self._parse_messages(raw_messages, scene.user_character.name)
        if scene.progress.progress >= 1 and scene.progress.length_strict:
            result.finished = True
        elif scene.progress.goal_check_requested and scene.progress.goal is not None:
            result.finished = self._parse_goal(self._exec(self.prompter.goal_check(scene)))
        if result.finished or scene.progress.finalization_requested:
            result.summary = self._exec(self.prompter.scene_summary(scene))
            result.cumulative_summary = self._exec(self.prompter.cumulative_summary(scene, result.summary))
        return result




