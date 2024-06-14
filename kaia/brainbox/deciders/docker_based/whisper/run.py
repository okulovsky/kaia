from kaia.brainbox.deciders.whisper.installer import WhisperInstaller, WhisperSettings
from unittest import TestCase
from kaia.infra.deployment import SilentExecutor
import time
from pathlib import Path

if __name__ == '__main__':
    settings = WhisperSettings()
    installer = WhisperInstaller(settings)
    executor = SilentExecutor()
    installer.install(executor)
    installer.self_test(TestCase())
