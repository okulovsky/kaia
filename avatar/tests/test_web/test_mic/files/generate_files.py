from avatar.utils.sine_wav import sine_wav
from pathlib import Path

FOLDER = Path(__file__).parent

if __name__ == '__main__':
    with open(FOLDER/'amp1000.wav', 'wb') as f:
        f.write(sine_wav(1000))
    with open(FOLDER/'amp2500.wav','wb') as f:
        f.write(sine_wav(2500))
    with open(FOLDER / 'amp5000.wav', 'wb') as f:
        f.write(sine_wav(5000))
