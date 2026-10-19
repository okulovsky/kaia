from datetime import datetime
from pathlib import Path
from chara.common import Chara
from chara.common.llm import BrainBoxLLMEngine, LLMSetup
from chara.nlu.datasets.negatives import NegativeCase, NegativePipeline, create_negative_request
from chara.nlu.datasets.text_dataset import LANGUAGES
from .common import default_ultimate_nlu_folder


def create_negatives(
        model: str = 'mistral-small',
        languages: tuple[str, ...] = LANGUAGES,
        batches_per_language: int = 5,
        folder: Path | None = None,
) -> Path:
    """
    Asks the LLM for phrases that are not commands, `batches_per_language` lists of them per language,
    in a new run in `folder`/negatives (or resumes the last run if it is unfinished),
    then rebuilds `folder`/negatives.txt from all the finished runs.
    The slots model learns to answer them with `intent: none`. Returns the path to negatives.txt.
    """
    if folder is None:
        folder = default_ultimate_nlu_folder()
    negatives_folder = folder/'negatives'

    runs = sorted(p for p in negatives_folder.iterdir() if p.is_dir()) if negatives_folder.is_dir() else []
    if len(runs) > 0 and not Chara.from_folder(runs[-1]).has_result:
        run = runs[-1]
    else:
        run = negatives_folder/('$' + datetime.now().isoformat())

    cases = [NegativeCase(language, index) for language in languages for index in range(batches_per_language)]
    pipeline = NegativePipeline(create_negative_request(LLMSetup(BrainBoxLLMEngine(), model)))
    Chara.start(run)
    phrases = Chara.call(pipeline)(cases)
    print(f'{len(phrases)} negatives in {run}')

    all_phrases = []
    for run in sorted(p for p in negatives_folder.iterdir() if p.is_dir()):
        run_folder = Chara.from_folder(run)
        if run_folder.has_result:
            all_phrases.extend(run_folder.result)
        else:
            print(f'Skipped unfinished run {run}')

    all_phrases = list(dict.fromkeys(all_phrases))
    negatives_path = folder/'negatives.txt'
    negatives_path.write_text('\n'.join(all_phrases))
    print(f'{len(all_phrases)} negatives in {negatives_path}')
    return negatives_path
