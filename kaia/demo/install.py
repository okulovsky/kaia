from brainbox import BrainBox
from brainbox.deciders import RhasspyKaldi, Whisper, OpenTTS

if __name__ == '__main__':
    with BrainBox.Api.Test() as api:
        for decider in [RhasspyKaldi, Whisper, OpenTTS]:
            api.controller_api.install(decider)
            api.controller_api.self_test(decider)