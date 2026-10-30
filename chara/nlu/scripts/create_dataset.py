import json
from datetime import datetime
from pathlib import Path
from grammatron import Template
from chara.common import Chara, CasePrioritization
from chara.paraphrasing.common import Paraphrase
from chara.nlu.datasets.text_dataset import TextDatasetPipeline, TextDatasetCase, TextDatasetPrioritization
from .common import default_ultimate_nlu_folder, LANGUAGES


MOODS = (
    'User speaks neutrally and clearly',
    'User speaks quickly and briefly, no filler words',
    "User is angry because of the previous unsuccessful attempts, speaks accordingly",
    "User is in a good mood and speaks with assistant as if it was a real person",
)


def create_dataset(
        templates: list[Template],
        model: str = 'mistral-small',
        variants_count: int = 5,
        folder: Path | None = None,
        languages: tuple[str, ...] = LANGUAGES,
        moods: tuple[str, ...] = MOODS,
        strategy: CasePrioritization.Strategy = CasePrioritization.Strategy.only_new,
        budget: int | None = None,
) -> Path:
    """
    Paraphrases `templates` in all `languages` and `moods` into a new run in `folder`/positives (or resumes the last run if it is unfinished).
    The run takes at most `budget` cases (no limit if None), chosen by `strategy` against what the finished runs already have:
    `only_new` takes only the combinations of template, language and mood that are not there yet, `expand` adds to the least covered ones.
    Then rebuilds `folder`/dataset.json from all the finished runs:
    the templates without parameters go as they are, the others get `variants_count` variants with random values.
    Returns the path to dataset.json.
    """
    if folder is None:
        folder = default_ultimate_nlu_folder()
    positives_folder = folder/'positives'

    runs = sorted(p for p in positives_folder.iterdir() if p.is_dir()) if positives_folder.is_dir() else []
    if len(runs) > 0 and not Chara.from_folder(runs[-1]).has_result:
        run = runs[-1]
    else:
        run = positives_folder/('$' + datetime.now().isoformat())

    cases = Paraphrase([
        TextDatasetCase(template, language, mood)
        for mood in moods
        for language in languages
        for template in templates
    ]).prepare()
    if budget is None:
        budget = len(cases.cases)
    prioritization = TextDatasetPrioritization(positives_folder, strategy, budget)
    Chara.start(run)
    cases = Chara.call(TextDatasetPipeline(model, prioritization))(cases)
    print(f'{len(cases)} templates in {run}')

    all_cases = []
    for run in sorted(p for p in positives_folder.iterdir() if p.is_dir()):
        run_folder = Chara.from_folder(run)
        if run_folder.has_result:
            all_cases.extend(run_folder.result)
        else:
            print(f'Skipped unfinished run {run}')

    records = TextDatasetPipeline.export(all_cases, variants_count)
    dataset_path = folder/'dataset.json'
    dataset_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f'{len(records)} records from {len(all_cases)} templates in {dataset_path}')
    return dataset_path
