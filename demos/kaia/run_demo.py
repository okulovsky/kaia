from demos.kaia.main import create_app
from demos.kaia.audio_control import MicSettings

mic_settings = MicSettings(
    mic_device_index=-1,
    sample_rate=16000,
    silence_level=2000
)

use_version_2 = True

if __name__ == '__main__':
    app = create_app(mic_settings=mic_settings, use_version_2=use_version_2)
    app.app.run()