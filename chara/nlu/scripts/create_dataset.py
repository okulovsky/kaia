import json
from datetime import datetime
from pathlib import Path
from grammatron import Template
from chara.common import Chara
from chara.nlu.datasets.text_dataset import TextDatasetPipeline, MOODS, LANGUAGES
from .common import default_ultimate_nlu_folder


def create_dataset(
        templates: list[Template],
        model: str = 'mistral-small',
        variants_count: int = 5,
        folder: Path | None = None,
) -> Path:
    """
    Paraphrases `templates` into a new run in `folder`/templates (or resumes the last run if it is unfinished),
    then rebuilds `folder`/dataset.json from all the finished runs:
    the templates without parameters go as they are, the others get `variants_count` variants with random values.
    Returns the path to dataset.json.
    """
    if folder is None:
        folder = default_ultimate_nlu_folder()
    templates_folder = folder/'templates'

    runs = sorted(p for p in templates_folder.iterdir() if p.is_dir()) if templates_folder.is_dir() else []
    if len(runs) > 0 and not Chara.from_folder(runs[-1]).has_result:
        run = runs[-1]
    else:
        run = templates_folder/('$' + datetime.now().isoformat())

    pipeline = TextDatasetPipeline(model, templates, list(LANGUAGES), list(MOODS))
    Chara.start(run)
    cases = Chara.call(pipeline.paraphrase)()
    print(f'{len(cases)} templates in {run}')

    all_cases = []
    for run in sorted(p for p in templates_folder.iterdir() if p.is_dir()):
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
