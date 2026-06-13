from chara.common.pipelines import upload_to_avatar
import pickle
from avatar.daemon import ParaphraseService, ParaphraseRecord
from typing import Iterable

def upload(records: Iterable[ParaphraseRecord], index_length: int = 4):
    records = list(records)
    package = pickle.dumps(records)
    upload_to_avatar(
        ParaphraseService,
        ParaphraseService.PARAPHRASES_PREFIX,
        ParaphraseService.PARAPHRASES_SUFFIX,
        index_length,
        package
    )


