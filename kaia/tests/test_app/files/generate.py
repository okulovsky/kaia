from brainbox import BrainBox
from brainbox.utils import TestSpeaker
from pathlib import Path

if __name__ == '__main__':
    with BrainBox.Api.Test() as api:
        speaker = TestSpeaker(api, 1)
        folder = Path(__file__).parent
        #speaker.speak('computer').to_file(folder/'computer.wav')
        #speaker.speak('Are you here?').to_file(folder/'are_you_here.wav')
        #speaker.speak('Repeat after me!').to_file(folder/'repeat_after_me.wav')
        #speaker.speak('Make me a sandwich').to_file(folder/'make_me_a_sandwich.wav')
        speaker.speak("")