import requests
from kaia.infra.marshalling_api import MarshallingEndpoint

class CoquiTTSApi:
    def __init__(self, address: str):
        MarshallingEndpoint.check_address(address)
        self.address = address


    def _raise_if_error(self, result, stage):
        if result.status_code == 500:
            raise ValueError(f"{stage}: CoquiTTS server returned {result.status_code}\n{result.text}")
        elif result.status_code != 200:
            raise ValueError(f"{stage}:, CoquiTTS server returned {result.status_code}")

    def load_model(self, model_name):
        result = requests.post(
            f'http://{self.address}/load_model',
            json=dict(model=model_name)
        )
        self._raise_if_error(result, f'When loading model {model_name}')
        return result.json()


    def run_request(self, endpoint, arguments):
        result = requests.post(
            f'http://{self.address}/{endpoint}',
            json = arguments
        )
        self._raise_if_error(result, f'When running model with arguments {arguments}')
        return result.content

    def _get_language(self, model_info, language):
        if language is None and model_info['languages'] is not None:
            language = model_info['languages'][0]
        if language is not None and model_info['languages'] is None:
            language = None
        return language

    def dub(self, model_info, text, voice, language=None):
        if not model_info['is_custom_model']:
            language = self._get_language(model_info, language)
            args = dict(text=text, speaker=voice, language=language)
            return self.run_request('run_model', args)
        else:
            args = dict(text = text, speaker_name = voice)
            return self.run_request('run_synthesizer', args)

    def voice_clone(self, model_info, text, voice, language = None):
        language = self._get_language(model_info, language)
        args = dict(text=text, speaker_wav=f'/data/voices/{voice}.wav', language=language)
        return self.run_request('run_model', args)
