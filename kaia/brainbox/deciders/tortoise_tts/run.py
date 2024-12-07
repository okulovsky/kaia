from kaia.brainbox.deciders.tortoise_tts.installer import TortoiseTTSSettings, TortoiseTTSInstaller, TortoiseTTS
from kaia.brainbox import BrainBox, BrainBoxTask
from unittest import TestCase
from pathlib import Path
import shutil

if __name__ == '__main__':
    settings = TortoiseTTSSettings()
    installer = TortoiseTTSInstaller(settings)
    installer.install()
    installer.notebook_service.run()