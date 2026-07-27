from datetime import date
from pathlib import Path
from brainbox.deciders import Ollama
from chara import Chara, CaseCollection
from chara.images.common import ActivityCase, ActivityCatalogPipeline, ActivityCatalogPipelineSettings


def run_activity_catalog(
        cases: list[ActivityCase],
        llm_model: str,
        yaml_path: Path,
        batch_size: int = 15,
        desired_activity_count: int = 30,
        lookahead_span: int = 3,
        options: Ollama.Options | None = None,
        ):
    for case in cases:
        case.batch_size = batch_size

    folder = Chara.Apis.content_folder / 'images/activities' / f'$pipeline_{date.today().isoformat()}'
    Chara.start(folder)
    settings = ActivityCatalogPipelineSettings(llm_model, yaml_path, desired_activity_count, lookahead_span, options)
    pipeline = ActivityCatalogPipeline(settings)
    return Chara.call(pipeline)(CaseCollection(cases))
