from typing import *
import requests
from urllib.parse import urlencode
from ....framework import IDecider, File, DockerWebServiceApi
from .settings import OpenTTSSettings
from .controller import OpenTTSController

class OpenTTS(DockerWebServiceApi[OpenTTSSettings, OpenTTSController]):
    def __init__(self, address: str = None):
        super().__init__(address)


    def voiceover(self,
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

    def __call__(self,
                  text: str,
                  voice: str = 'coqui-tts:en_vctk',
                  lang: str = 'en',
                  speakerId: Optional[str] = 'p256'
                  ):
        return self.voiceover(text,voice,lang,speakerId)

    Controller = OpenTTSController
    Settings = OpenTTSSettings