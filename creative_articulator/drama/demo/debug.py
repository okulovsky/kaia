import argparse
from pathlib import Path

from chara.common.llm import BrainBoxLLMEngine, LLMSetup

from creative_articulator.drama.data import Message, Node
from creative_articulator.drama.demo.characters import CHARACTERS, DEFAULT_PROTAGONIST, get_character
from creative_articulator.drama.demo.scenes import SCENES
from creative_articulator.drama.demo.story import build_story
from creative_articulator.drama.driver import AddMessageDiff, IEngine, SceneState, StoryState
from creative_articulator.drama.scene import ISceneRules, SceneEngine

MODEL = 'gemma3:27b-it-q4_K_M'


def run_scene(story: Node, scene_node: Node) -> list[str]:
    story[StoryState].current_node = scene_node
    actors = scene_node[ISceneRules].get_actors()
    if actors.opening is not None:
        AddMessageDiff(Message.from_text(actors.opening)).apply(story)

    SceneEngine.scene_engine_debug_run(scene_node[IEngine], scene_node)

    state = scene_node[SceneState]
    lines = [str(message) for message in state.messages]
    if state.summary is not None:
        lines.append('')
        lines.append(f'[summary] {state.summary}')
    return lines


def run(character: str, model: str = MODEL, scenes=SCENES, output: Path | None = None) -> str:
    protagonist = get_character(character)
    llm = LLMSetup(BrainBoxLLMEngine(), model)
    scenes = tuple(scenes)
    story = build_story(protagonist, llm, scenes)

    lines = [f'Prostokvashino, with {protagonist.name} played automatically as the protagonist.', '']
    for scene, scene_node in zip(scenes, story.children):
        lines.append(f'=== {scene.title} ===')
        lines.append('')
        lines.extend(run_scene(story, scene_node))
        lines.append('')

    script = '\n'.join(lines)
    print(script)
    if output is not None:
        output.write_text(script)
        print(f'written to {output}')
    return script


def main():
    parser = argparse.ArgumentParser(description='Generate the Prostokvashino script without a human in the loop.')
    parser.add_argument('character', nargs='?', default=DEFAULT_PROTAGONIST.name,
                        choices=[c.name for c in CHARACTERS],
                        help='the character the engine plays as the protagonist')
    parser.add_argument('--model', default=MODEL)
    parser.add_argument('--scene', choices=[s.title for s in SCENES], help='run a single scene instead of all of them')
    parser.add_argument('--output', type=Path, help='also write the script to this file')
    args = parser.parse_args()

    scenes = SCENES if args.scene is None else tuple(s for s in SCENES if s.title == args.scene)
    run(args.character, args.model, scenes, args.output)


if __name__ == '__main__':
    main()
