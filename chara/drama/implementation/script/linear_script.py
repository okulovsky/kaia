from .character_script import CharacterScript
from .scene_script import SceneScript
from dataclasses import dataclass
from .file_manager import FileManager
from ..scene import Medium, Scene, Character, CharacterPriority, Message, SceneProgress, SceneContext
from .past_scene import PastPlay
from yo_fluq import *
from brainbox.flow import JinjaPrompter


@dataclass
class LinearScript:
    intro: JinjaPrompter[dict[str,str]]
    user_character: str
    name_to_character: dict[str, CharacterScript]
    role_to_character_name: dict[str, str]
    scenes: tuple[SceneScript,...]

    @staticmethod
    def parse_script(manager: FileManager):
        scenes = SceneScript.parse_scenes(manager)
        data = manager.parse_yaml(manager.sections["Intro"])
        user_character = data['user_character']
        intro = JinjaPrompter(data['intro'])
        role_to_character = CharacterScript.parse_characters(manager)
        name_to_character = {z.name: z for z in role_to_character.values()}
        role_to_character_name = {k:v.name for k, v in role_to_character.items()}

        return LinearScript(
            intro,
            user_character,
            name_to_character,
            role_to_character_name,
            tuple(scenes)
        )

    def _generate_progress(self, script: SceneScript, play: PastPlay) -> SceneProgress:
        progress = SceneProgress()
        current_message_count = len([c for c in play.unfinished_scene.messages_only() if c.name==self.user_character])
        if script.length is not None:
            progress.progress = current_message_count/script.length
            progress.goal_check_requested = progress.progress > 0.5
        progress.goal = script.goal(self.role_to_character_name) if script.goal is not None else None
        progress.finalization_requested = play.request is not None
        progress.length_strict = script.length_strict
        return progress

    def _generate_context(self, script: SceneScript, play: PastPlay):
        context = SceneContext()
        context.previous_summaries = [s for scene in play.past_scenes for s in scene.find_tags('summary')]
        cumulative_summaries = [s for scene in play.past_scenes for s in scene.find_tags('cumulative_summary')]
        if len(cumulative_summaries) != len(context.previous_summaries):
            raise ValueError("Length of the cumulative summaries does not match the length of summaries")

        intro = self.intro(self.role_to_character_name)
        if len(context.previous_summaries) == 0:
            context.intro = intro
        else:
            last = "In the last scene: " + context.previous_summaries[-1]
            if len(context.previous_summaries) == 1:
                context.intro = f"{intro}\n\n{last}"
            else:
                context.intro = f"{cumulative_summaries[-2]}\n\n{last}"
        context.scene_intro = script.intro(self.role_to_character_name)
        context.medium = script.medium
        context.intermediate_summaries = tuple(play.unfinished_scene.find_tags('intermediate_summary'))
        return context

    def generate_scene(self, play: PastPlay):
        current_scene_index = len(play.past_scenes)
        if current_scene_index >= len(self.scenes):
            raise ValueError(f"Scene #{current_scene_index} is requested, but there are only {len(self.scenes)}")
        script: SceneScript = self.scenes[current_scene_index]

        result = Scene()
        result.progress = self._generate_progress(script, play)
        result.context = self._generate_context(script, play)

        result.user_character = Character(self.user_character, self.name_to_character[self.user_character].description)
        characters = []
        for role, name in self.role_to_character_name.items():
            if role not in script.roles:
                continue
            if name == self.user_character:
                continue
            co = self.name_to_character[name]
            characters.append(Character(
                name,
                co.description,
                CharacterPriority.Leading,
                co.get_style(script.medium)
            ))
        result.characters = tuple(characters)

        messages = []
        for element in play.unfinished_scene.messages:
            if isinstance(element, Message):
                messages.append(element)
            else:
                messages = messages[-5:]
        result.messages = tuple(messages)
        return result





