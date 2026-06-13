from ..architecture import logger, Chara
from avatar.daemon import ParaphraseService

def upload_to_avatar(service, prefix: str, suffix:str, index_length: int, data):
    logger.log(f"Uploading paraphrases to avatar server. Searching for a filename")

    rs = Chara.Apis.avatar_api.resources(service).list('/')
    index = 0
    while True:
        index_str = str(index).zfill(index_length)
        filename = f'{prefix}-{index_str}{suffix}'
        if rs is None:
            logger.log(f"No files, {filename} is available")
            break
        if filename not in rs:
            logger.log(f"Filename {filename} is available")
            break
        logger.log(f"Filename {filename} is taken")
        index += 1
    logger.log("Uploading...")
    Chara.Apis.avatar_api.resources(service).upload(filename, data)
    logger.log("Uploaded")