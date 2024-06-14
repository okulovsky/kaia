import time
from kaia.infra import SilentExecutor
from kaia.brainbox.deciders.coqui_tts.decider import CoquiTTS, CoquiTTSSettings
from unittest import TestCase



if __name__ == '__main__':
    settings = CoquiTTSSettings()
    decider = CoquiTTS(settings)
    decider.install(SilentExecutor(), True)
    #decider.self_test(TestCase())
    decider.run_notebook(False)




