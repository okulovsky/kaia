import time

from kaia.kaia.audio_control.wav_streaming import WavStreamingApi, WavApiSettings
from pathlib import Path
from uuid import uuid4
import requests
from pprint import pprint
from uuid import uuid4

if __name__ == '__main__':
    file_path = Path(__file__).parent/'files/send/timer.wav'
    target_id = str(uuid4())
    sample_rate = WavStreamingApi.get_file_framerate(file_path)
    print(sample_rate)
    api = WavStreamingApi(WavApiSettings(sample_rate=sample_rate))
    api.send_file_right_away(file_path, target_id)

    address = f'http://127.0.0.1:8890'
    session_id = str(uuid4())
    print(requests.post(f"{address}/command/{session_id}/command_initialize", json=''))
    print(requests.post(f"{address}/command/{session_id}/audio_command", json=dict(filename=target_id)))

    time.sleep(1)
    updates = requests.get(f'{address}/updates/{session_id}/-1').json()
    pprint(updates)
