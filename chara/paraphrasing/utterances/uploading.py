from chara.common import logger, CharaApis
from avatar.daemon import ParaphraseService, ParaphraseRecord
import pickle

def upload(records: list[ParaphraseRecord], index_length: int = 4):
    logger.log(f"Uploading paraphrases to avatar server. Searching for a filename")

    rs = CharaApis.avatar_api.resources(ParaphraseService).list()
    index = 0
    while True:
        filename = (
                ParaphraseService.PARAPHRASES_PREFIX +
                '-' +
                str(index).zfill(index_length) +
                ParaphraseService.PARAPHRASES_SUFFIX
        )
        if rs is None:
            logger.log(f"No files, {filename} is available")
            break
        if filename not in rs:
            logger.log(f"Filename {filename} is available")
            break
        logger.log(f"Filename {filename} is taken")
        index += 1

    package = pickle.dumps(records)
    CharaApis.avatar_api.resources(ParaphraseService).upload(package, filename)