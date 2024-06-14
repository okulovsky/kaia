from unittest import TestCase
from ....infra import Loc

def check_if_its_sound(content, tc: TestCase):
    import soundfile as sf
    with Loc.create_temp_file('self_check', 'wav') as fname:
        with open(fname, 'wb') as file:
            file.write(content)
        f = sf.SoundFile(fname)
        duration = f.frames / f.samplerate
        tc.assertGreater(duration, 1)
        f.close()