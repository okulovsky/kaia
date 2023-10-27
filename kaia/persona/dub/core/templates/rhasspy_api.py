from typing import *
import requests
from .rhasspy_handler import RhasspyHandler
from pathlib import Path
import subprocess
from kaia.infra import Loc
from .template import Utterance, Template

class RhasspyRequests:
    def __init__(self, address: str, timeout=5):
        if not address.endswith('/'):
            address += '/'
        self.address = address
        self.timeout = timeout


    def train_request(self, ini: str):
        result = ''
        reply = requests.post(self.address + 'api/sentences', data=ini)
        if reply.status_code != 200:
            raise ValueError(f'Rhasspy failed to accept sentences\n{reply.text}')
        result += reply.text + '\n\n'

        reply = requests.post(self.address + "api/train")
        if reply.status_code != 200:
            raise ValueError(f'Rhasspy failed to train\n{reply.text}')
        result += reply.text

        return result


    def recode(self, file: Path, output_file: Optional[Path] = None):
        if output_file is None:
            name_parts = file.name.split('.')
            output_name = '.'.join(name_parts[:-1]) + '.recoded.wav'
            output_file = file.parent / output_name
        subprocess.call([
            Loc.get_ffmpeg(),
            '-i',
            file,
            output_file,
            '-y'
        ])
        return output_file

    def recognize_request(self, file, recode: bool = False):
        if recode:
            with Loc.temp_file('rhasspy_api_recode','wav') as tmp:
                self.recode(file, tmp)
                with open(tmp,'rb') as stream:
                    return self.recognize_bytes(stream.read(), False)
        else:
            with open(file, 'rb') as stream:
                data = stream.read()
                return self.recognize_bytes(data, False)

    def recognize_bytes(self, data: bytes, recode: bool = False):
        if recode:
            with Loc.temp_file('rhasspy_api_recode','ogg') as tmp:
                with open(tmp, 'wb') as stream:
                    stream.write(data)
                with Loc.temp_file('rhasspy_api_recode', 'wav') as tmp_wav:
                    self.recode(tmp, tmp_wav)
                    with open(tmp_wav, 'rb') as wav_stream:
                        data = wav_stream.read()

        reply = requests.post(self.address + 'api/speech-to-intent', data=data, timeout=self.timeout)
        if reply.status_code != 200:
            raise ValueError(f'Rhasspy failed to recognize bytes\n{reply.text}')
        return reply.json()



class RhasspyAPI:
    def __init__(self, requests: RhasspyRequests, handler: RhasspyHandler):
        self.handler = handler
        self.requests = requests

    def train(self):
        ini = self.handler.ini_file
        return self.requests.train_request(ini)

    def recognize(self, file, recode: bool = False) -> Optional[Utterance]:
        if isinstance(file, Path) or isinstance(file, str):
            reply = self.requests.recognize_request(file, recode)
        elif isinstance(file, bytes) or isinstance(file, bytearray):
            reply = self.requests.recognize_bytes(file, recode)
        else:
            raise ValueError(f'`file` must be str, Path, bytes, but was {type(file)}')
        self.last_recognition_ = reply
        return self.handler.parse_json(reply)

    @staticmethod
    def create(address: str, intents: Iterable[Template]):
        return RhasspyAPI(RhasspyRequests(address), RhasspyHandler(intents))




