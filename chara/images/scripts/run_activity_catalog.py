from pathlib import Path
from brainbox.deciders import Ollama
from chara import Chara, CaseCollection, CasePrioritization
from chara.images.common import ActivityCase, ActivityCatalogPipeline, ActivityCatalogPipelineSettings


def run_activity_catalog(
        cases: list[ActivityCase],
        llm_model: str,
        yaml_path: Path,
        strategy: CasePrioritization.Strategy,
        budget: int,
        batch_size: int = 15,
        lookahead_span: int = 3,
        options: Ollama.Options | None = None,
        ):
    for case in cases:
        case.batch_size = batch_size

    Chara.start_or_resume(Chara.Apis.content_folder / 'images/activities', '$pipeline_')
    settings = ActivityCatalogPipelineSettings(llm_model, yaml_path, strategy, budget, lookahead_span, options)
    pipeline = ActivityCatalogPipeline(settings)
    return Chara.call(pipeline)(CaseCollection(cases))
