from dataclasses import dataclass
from datetime import date
from pathlib import Path
from brainbox.deciders import Ollama
from chara import Chara, CaseCollection, CasePrioritization
from chara.common.llm import BrainBoxLLMEngine, BulletPointDivider, LLMSetup
from .case import ActivityCase
from .activity_catalog_item import ActivityCatalogItem
from .activity_prioritization import ActivityPrioritization
from .lookahead import is_theme_within_lookahead


@dataclass
class ActivityCatalogPipelineSettings:
    llm_model: str
    activities_path: Path
    strategy: CasePrioritization.Strategy
    budget: int
    lookahead_span: int = 3
    options: Ollama.Options | None = None


class ActivityCatalogPipeline:
    def __init__(self, settings: ActivityCatalogPipelineSettings):
        self.settings = settings

    def __call__(self, cases: CaseCollection[ActivityCase]) -> CaseCollection[ActivityCase]:
        path = self.settings.activities_path
        catalog = ActivityCatalogItem.read_catalog(path)

        today = date.today()
        relevant = [
            c for c in cases.successes
            if is_theme_within_lookahead(c.theme, today, self.settings.lookahead_span)
        ]

        for case in relevant:
            item = catalog.get(case.to_fingerprint())
            if item is not None:
                for activity in item.activities:
                    if activity not in case.activities:
                        case.activities.append(activity)

        prioritization = ActivityPrioritization(catalog, self.settings.strategy, self.settings.budget)
        prioritized = Chara.call(prioritization, 'prioritization')(CaseCollection(relevant))
        to_generate = prioritized.successes
        not_selected = prioritized.errors

        def merge(case: ActivityCase, result: str) -> None:
            for activity in BulletPointDivider()(result):
                if activity not in case.activities:
                    case.activities.append(activity)

        if len(to_generate) > 0:
            setup = LLMSetup(BrainBoxLLMEngine(), self.settings.llm_model)
            request = (setup
                       .default()
                       .template('activity.jinja', (Path(__file__).parent,))
                       .options(self.settings.options)
                       .parse(merge)
                       .to_request())
            generation_pipeline = request.create_brainbox_pipeline()
            generated = Chara.call(generation_pipeline, 'generate')(CaseCollection(to_generate))
        else:
            generated = CaseCollection(to_generate)

        result = CaseCollection(generated, not_selected, cases.errors)

        for case in result.successes:
            fingerprint = case.to_fingerprint()
            catalog[fingerprint] = ActivityCatalogItem(fingerprint, list(case.activities))

        ActivityCatalogItem.write_catalog(path, catalog)

        return result
