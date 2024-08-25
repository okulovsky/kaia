import requests
from kaia.infra.marshalling_api import MarshallingEndpoint
from ...core import IApiDecider, File

class CoquiTTS(IApiDecider):
    def __init__(self, address: str, model_info):
        MarshallingEndpoint.check_address(address)
        self.address = address
        self.model_info = model_info

    def _raise_if_error(self, result, stage):
        if result.status_code == 500:
            raise ValueError(f"{stage}: CoquiTTS server returned {result.status_code}\n{result.text}")
        elif result.status_code != 200:
            raise ValueError(f"{stage}:, CoquiTTS server returned {result.status_code}")

    def _run_request(self, endpoint, arguments):
        result = requests.post(
            f'http://{self.address}/{endpoint}',
            json = arguments
        )
        self._raise_if_error(result, f'When running model with arguments {arguments}')
        return File(self.current_job_id+'.output.wav', result.content, File.Kind.Audio)

    def _get_language(self, model_info, language):
        if language is None and model_info['languages'] is not None:
            language = model_info['languages'][0]
        if language is not None and model_info['languages'] is None:
            language = None
        return language

    def dub(self, text, voice = None, language=None):
        if not self.model_info['is_custom_model']:
            language = self._get_language(self.model_info, language)
            if voice is None and self.model_info['speakers'] is not None:
                voice = self.model_info['speakers'][0]
            args = dict(text=text, speaker=voice, language=language)
            return self._run_request('run_model', args)
        else:
            if voice is None and self.model_info['speakers'] is not None:
                voice = self.model_info['speakers'][0]
            args = dict(text = text, speaker_name = voice)
            return self._run_request('run_synthesizer', args)

    def voice_clone(self, text, voice, language = None):
        language = self._get_language(self.model_info, language)
        args = dict(text=text, speaker_wav=f'/data/voices/{voice}.wav', language=language)
        return self._run_request('run_model', args)



class CoquiTTSExtendedAPI(CoquiTTS):
    def __init__(self, address):
        super().__init__(address, None)

    def load_model(self, model_name):
        result = requests.post(
            f'http://{self.address}/load_model',
            json=dict(model=model_name)
        )
        self._raise_if_error(result, f'When loading model {model_name}')
        self.model_info = result.json()
        return self.model_info


    def get_loaded_model(self):
        reply = requests.get(f'http://{self.address}/get_loaded_model')
        try:
            return reply.json()
        except:
            raise ValueError(f"Wrong answer {reply.status_code}\n{reply.text}")



