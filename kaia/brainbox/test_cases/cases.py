from .brainbox_test_cases import DubbingBrainBoxTestCase
from kaia.brainbox.core import BrainBoxTask

TEXT = 'The quick brown fox jumps over the lazy dog'

def create_cases():
    yield DubbingBrainBoxTestCase(
        'TortoiseTTS/Whisper',
        3,
        BrainBoxTask(
            id = BrainBoxTask.safe_id(),
            decider = 'TortoiseTTS',
            arguments = dict(text=TEXT, voice='test_voice')
        )
    )

    yield DubbingBrainBoxTestCase(
        'OpenTTS/Whisper',
        1,
        BrainBoxTask(
            id = BrainBoxTask.safe_id(),
            decider = 'OpenTTS',
            arguments = dict(text=TEXT)
        )
    )

    yield DubbingBrainBoxTestCase(
        'CoquiTTS/Whisper',
        1,
        BrainBoxTask(
            id = BrainBoxTask.safe_id(),
            decider = 'CoquiTTS',
            decider_parameters='tts_models/en/vctk/vits',
            decider_method='dub',
            arguments=dict(text=TEXT, voice='p226')
        )
    )