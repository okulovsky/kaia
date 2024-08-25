from typing import *
import requests
from urllib.parse import urlencode
from kaia.infra.marshalling_api import MarshallingEndpoint
from ...core import IApiDecider, File

class OpenTTS(IApiDecider):
    def __init__(self, address: str):
        MarshallingEndpoint.check_address(address)
        self.address = address

    def __call__(self,
                 text: str,
                 voice: str = 'coqui-tts:en_vctk',
                 lang: str = 'en',
                 speakerId: Optional[str] = 'p256'
             ):
        parameters = dict(text=text, voice=voice, lang=lang, speakerId=speakerId)
        query_string = urlencode(parameters)
        reply = requests.get(f'http://{self.address}/api/tts?' + query_string)
        if reply.status_code != 200:
            raise ValueError(f'OpenTTS server returned {reply.status_code}\n{reply.text}')
        result = File(self.current_job_id+'.output.wav', reply.content, File.Kind.Audio)
        return result