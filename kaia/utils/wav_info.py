import wave
from loguru import logger
from pathlib import Path




def wav_check(path: Path | str):
    with wave.open(str(path), 'rb') as f:
        logger.info(f"Channels: {f.getnchannels()}")
        logger.info(f"Sample Rate: {f.getframerate()}")
        logger.info(f"Frame Count: {f.getnframes()}")
        logger.info(f"Sample Width: {f.getsampwidth()}")


