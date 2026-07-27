from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from chara import Chara, CaseCollection, ICasePipeline
from chara.images.common import (
    ImageSetup, ImageRequest, IImageScenario, ScenarioPipeline, ShotPipeline,
    DrawingCase, DrawingPipeline, ReviewSetup, GenerationPipeline,
)
from chara.images.krea import KreaCase, KreaSettings, KreaImageToImage, KreaPipelineFactory


def _find_last_generation_folder(generation_root: Path) -> Path|None:
    candidates = [p for p in generation_root.iterdir() if p.is_dir()] if generation_root.is_dir() else []
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.name)


def generate_and_upload_images(
        setups: list[ImageSetup],
        budget: int,
        case_factory: Callable[[ImageRequest], IImageScenario]|None = None,
        *,
        character_cards: str|None = None,
        steps: list[tuple[str, ICasePipeline]] | None = None,
        variant_pipelines: dict[str, Callable[[CaseCollection[DrawingCase]], CaseCollection[DrawingCase]]] | None = None,
        review_setup: ReviewSetup | None = None,
        report_groups: tuple[Callable[[DrawingCase], Any], ...] = (),
        llm_model: str = 'mistral-small',
        script_folders: tuple[Path, ...] = (),
):
    """Generates images for the given setups within budget, then uploads and packages
    them to whatever Chara.Apis.avatar_api currently points to. If steps isn't passed,
    it defaults to the scene/clothing/face/shot pipelines built from a KreaPipelineFactory
    - the same factory case_factory defaults to, so the templates it needs are found.

    If the most recently created folder under images/generation wasn't completed (no
    top-level result yet), it's resumed automatically - Chara.start() picks back up from
    whatever phases already have a cached result there, so already-generated images
    aren't redone. Otherwise, a fresh run folder is started."""

    activities_file = Chara.Apis.content_folder / 'images/activities/activities.yaml'

    if steps is None:
        factory = KreaPipelineFactory(llm_model, script_folders)
        steps = [
            ('scene', factory.create_scene_pipeline(1.2)),
            ('clothing', factory.create_clothing_pipeline(1.2)),
            ('face', factory.create_face_pipeline(1.2)),
            ('shot', ShotPipeline()),
        ]

    if character_cards is None:
        character_cards = str(Chara.Apis.content_folder/'images/character_cards/cards/{}.png')

    def _default_factory(request: ImageRequest):
        settings = KreaSettings(KreaImageToImage('', '', width=1024, height=1024,), name_to_source_filename_template=character_cards)
        return KreaCase(request.setup.character, settings, request.setup.theme, request.activity)
    if case_factory is None:
        case_factory = _default_factory

    scenario_pipeline = ScenarioPipeline(case_factory, steps)
    drawing_pipeline = DrawingPipeline(review_setup, variant_pipelines)
    pipeline = GenerationPipeline(activities_file, budget, scenario_pipeline, drawing_pipeline, report_groups)

    generation_root = Chara.Apis.content_folder / 'images/generation'
    last_folder = _find_last_generation_folder(generation_root)
    if last_folder is not None and not Chara.from_folder(last_folder).has_result:
        folder = last_folder
    else:
        folder = generation_root / ('$' + datetime.now().isoformat())
    Chara.start(folder)
    Chara.call(pipeline)(setups)
