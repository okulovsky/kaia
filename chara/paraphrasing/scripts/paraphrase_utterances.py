from pathlib import Path

from chara.common import Chara, CasePrioritization
from chara.common.llm import BrainBoxLLMEngine, LLMSetup
from chara.paraphrasing.common import Paraphrase
from chara.paraphrasing.utterances import (
    ParaphrasePrioritization, UtteranceParaphraseCaseManager, UtteranceParaphrasePipeline,
    create_default_utterance_request,
)
from avatar.daemon.paraphrase_service import ParaphraseRecord


def paraphrase_utterances(
        manager: UtteranceParaphraseCaseManager,
        strategy: CasePrioritization.Strategy,
        budget: int,
        *,
        llm_model: str = 'mistral-small',
        settings: Paraphrase.Settings|None = None,
        folder: Path|None = None,
) -> list[ParaphraseRecord]:
    """Paraphrases utterances and uploads them to the avatar.

    The `manager` says what content exists -- which templates, characters, users and
    languages -- and `strategy` and `budget` say which of these cases this run paraphrases:

        paraphrase_utterances(manager, CasePrioritization.Strategy.only_new, 100)
        paraphrase_utterances(manager, CasePrioritization.Strategy.expand, 100)

    A run selects once and stops; a big job is several runs.

    Runs are kept under `paraphrasing/<strategy>`, so one strategy never resumes
    another's folder. If the most recent run there never finished, it is resumed:
    Chara.start() picks back up from whatever phases already have a cached result, so
    cases already paraphrased are not paid for twice.
    """

    if settings is None:
        settings = Paraphrase.Settings(
            paraphrase_request=create_default_utterance_request(LLMSetup(BrainBoxLLMEngine(), llm_model)),
            enable_words_translation=False,
            grammar_correction_attempts=None,
        )

    if folder is None:
        Chara.start_or_resume(Chara.Apis.content_folder/'paraphrasing'/strategy.value, '$')
    else:
        Chara.start(folder)
    prioritization = ParaphrasePrioritization(strategy, budget)
    return Chara.call(UtteranceParaphrasePipeline(manager, settings, prioritization))()
