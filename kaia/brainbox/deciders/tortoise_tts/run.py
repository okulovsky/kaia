from kaia.brainbox.deciders.tortoise_tts.installer import TortoiseTTSSettings, TortoiseTTSInstaller, TortoiseTTS
from kaia.brainbox import BrainBox, BrainBoxTask
from unittest import TestCase
from pathlib import Path
import shutil

if __name__ == '__main__':
    settings = TortoiseTTSSettings()
    installer = TortoiseTTSInstaller(settings)

    with BrainBox().create_test_api() as api:
        for s in [
            "That quick beige fox jumped in the air over each thin dog.",
            "Look out, I shout, for he's foiled you again, creating chaos.",
        ]:
            result = api.execute(BrainBoxTask.call(TortoiseTTS).dub(text=s, voice='test_voice'))
            for file in result:
                shutil.copy(api.cache_folder/file.name, Path(__file__).parent)
