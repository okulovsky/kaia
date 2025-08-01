from phonix.tests.test_daemon.test_deamon.common import *
from brainbox.utils import WavProcessor

if __name__ == '__main__':
    proc = WavProcessor(PATH / 'computer.wav')
    silence = proc.create_silence(1)
    signal = proc.create_sine_wave(440, 3)

    frames = WavProcessor.combine(proc.frames, silence, signal, silence)
    bytes = proc.frames_to_wav_bytes(frames)
    FileIO.write_bytes(bytes, PATH/'computer_and_signal.wav')

