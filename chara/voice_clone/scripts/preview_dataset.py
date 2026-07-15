from typing import Iterable
from chara import Chara, Language
from ..distillation.dataset import (
    Corpus,
    PreviewDatasetPipeline,
    TypographicReplacement,
    BadSymbolsFilter,
    LengthFilter,
    TooMuchCapitalLettersFilter,
    NoAbbreviationsFilter,
)


def _default_corpus() -> Corpus:
    language = Language.English()
    return Corpus([
        TypographicReplacement.from_language(language),
        BadSymbolsFilter.from_language(language),
        LengthFilter(80, 100),
        TooMuchCapitalLettersFilter(4),
        NoAbbreviationsFilter.from_language(language),
    ])


def preview_dataset(raw_dataset: Iterable[str], language: Language, corpus: Corpus|None = None):
    if corpus is None:
        corpus = _default_corpus()

    folder = Chara.Apis.content_folder / 'voice_clone_dataset' / language.code / '$preview'
    Chara.start(folder)
    pipeline = PreviewDatasetPipeline(corpus, language)
    return Chara.call(pipeline)(raw_dataset)
