from typing import *
import requests
from .rhasspy_handler import RhasspyHandler
from pathlib import Path
import subprocess
from kaia.infra import Loc, MarshallingEndpoint
from .template import Utterance, Template


class RhasspyAPI:
    def __init__(self,
                 address: str | None,
                 intents: Optional[Iterable[Template]] = None,
                 timeout: int = 5
                 ):
        if address is not None:
            MarshallingEndpoint.check_address(address)
        self.address = address
        self.handler: None|RhasspyHandler = None
        if intents is not None:
            self.handler = RhasspyHandler(intents)
        self.timeout = timeout
        self.last_set_volume = None


    def setup_intents(self, intents: Iterable[Template]):
        self.handler = RhasspyHandler(intents)


    def train_ini(self, ini: str):
        result = ''
        reply = requests.post(f'http://{self.address}/api/sentences', data=ini)
        if reply.status_code != 200:
            raise ValueError(f'Rhasspy failed to accept sentences\n{reply.text}')
        result += reply.text + '\n\n'

        reply = requests.post(f'http://{self.address}/api/train')
        if reply.status_code != 200:
            raise ValueError(f'Rhasspy failed to train\n{reply.text}')
        result += reply.text

        return result


    def train(self):
        ini = self.handler.ini_file
        return self.train_ini(ini)


    def recognize(self, file, recode: bool = False) -> Optional[Utterance]:
        if isinstance(file, Path) or isinstance(file, str):
            reply = self.recognize_request(file, recode)
        elif isinstance(file, bytes) or isinstance(file, bytearray):
            reply = self.recognize_bytes(file, recode)
        else:
            raise ValueError(f'`file` must be str, Path, bytes, but was {type(file)}')
        self.last_recognition_ = reply
        return self.handler.parse_json(reply)


    def recode(self, file: Path, output_file: Optional[Path] = None):
        if output_file is None:
            name_parts = file.name.split('.')
            output_name = '.'.join(name_parts[:-1]) + '.recoded.wav'
            output_file = file.parent / output_name
        subprocess.call([
            'ffmpeg',
            '-i',
            file,
            output_file,
            '-y'
        ])
        return output_file

    def recognize_request(self, file, recode: bool = False):
        if recode:
            with Loc.create_temp_file('rhasspy_api_recode', 'wav') as tmp:
                self.recode(file, tmp)
                with open(tmp,'rb') as stream:
                    return self.recognize_bytes(stream.read(), False)
        else:
            with open(file, 'rb') as stream:
                data = stream.read()
                return self.recognize_bytes(data, False)

    def recognize_bytes(self, data: bytes, recode: bool = False):
        if recode:
            with Loc.create_temp_file('rhasspy_api_recode', 'ogg') as tmp:
                with open(tmp, 'wb') as stream:
                    stream.write(data)
                with Loc.create_temp_file('rhasspy_api_recode', 'wav') as tmp_wav:
                    self.recode(tmp, tmp_wav)
                    with open(tmp_wav, 'rb') as wav_stream:
                        data = wav_stream.read()

        reply = requests.post(f'http://{self.address}/api/speech-to-intent', data=data, timeout=self.timeout)
        if reply.status_code != 200:
            raise ValueError(f'Rhasspy failed to recognize bytes\n{reply.text}')
        return reply.json()


    def play_wav(self, data: bytes):
        reply = requests.post(
            f"http://{self.address}/api/play-wav",
            data=data,
            headers={'Content-Type': 'audio/wav'}
        )
        return reply

    def set_volume(self, volume: float):
        reply = requests.post(
            f'http://{self.address}/api/set-volume',
            data = str(volume),
            headers={'Content-Type': 'text/plain'}
        )
        self.last_set_volume = volume
        return reply

