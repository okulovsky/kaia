from datetime import datetime
from pathlib import Path

from chara.common import Chara
from chara.common.llm import BrainBoxLLMEngine, LLMSetup
from chara.paraphrasing.common import Paraphrase
from chara.paraphrasing.utterances import (
    ICaseSelection, UtteranceParaphraseCaseManager, UtteranceParaphrasePipeline,
    create_default_utterance_request,
)
from avatar.daemon.paraphrase_service import ParaphraseRecord


def _find_last_run_folder(root: Path) -> Path|None:
    candidates = [p for p in root.iterdir() if p.is_dir()] if root.is_dir() else []
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.name)


def paraphrase_utterances(
        manager: UtteranceParaphraseCaseManager,
        selection: ICaseSelection,
        *,
        llm_model: str = 'mistral-small',
        settings: Paraphrase.Settings|None = None,
        folder: Path|None = None,
) -> list[ParaphraseRecord]:
    """Paraphrases utterances and uploads them to the avatar.

    Two arguments decide everything. The `manager` says what content exists -- which
    templates, characters, users and languages -- and the `selection` says what this
    run generates out of it and when it stops:

        paraphrase_utterances(manager, NewEntitiesSelection())
        paraphrase_utterances(manager, DeficitSelection(budget=500))

    Runs are kept under `paraphrasing/<selection name>`, so one behaviour never resumes
    another's folder. If the most recent run there never finished, it is resumed:
    Chara.start() picks back up from whatever phases already have a cached result, so
    batches already paraphrased are not paid for twice.
    """

    if settings is None:
        settings = Paraphrase.Settings(
            paraphrase_request=create_default_utterance_request(LLMSetup(BrainBoxLLMEngine(), llm_model)),
            enable_words_translation=False,
            grammar_correction_attempts=None,
        )

    if folder is None:
        root = Chara.Apis.content_folder/'paraphrasing'/selection.name
        last = _find_last_run_folder(root)
        if last is not None and not Chara.from_folder(last).has_result:
            folder = last
        else:
            folder = root/('$' + datetime.now().isoformat())

    Chara.start(folder)
    return Chara.call(UtteranceParaphrasePipeline(manager, settings, selection))()
