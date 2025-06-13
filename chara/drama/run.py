from brainbox import BrainBox
from chara.drama import Prompter, SceneProcessor, SceneProcessorSettings, FileManager, PastPlay, LinearScript
from pathlib import Path

FILE = 'organizing_party.txt'


if __name__ == '__main__':
    api = BrainBox.Api('127.0.0.1:8090')
    prompter = Prompter(None, 0.6)
    settings = SceneProcessorSettings(api, 'mistral-small', 20, ('next', 'goal'), ('next', 'goal'))
    processor = SceneProcessor(settings, prompter)
    manager = FileManager(FILE, Path('characters.yaml'))
    script = LinearScript.parse_script(manager)
    past = PastPlay.parse(manager)
    scene = script.generate_scene(past)
    result = processor.process(scene)
    manager.append_to_file(result.next_messages, result.get_tags())




