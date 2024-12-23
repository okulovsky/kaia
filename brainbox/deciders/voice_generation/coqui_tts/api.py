import requests
from ....framework import BrainBoxApi, DockerWebServiceApi, File
from .controller import CoquiTTSController
from .settings import CoquiTTSSettings
from pathlib import Path

class CoquiTTS(DockerWebServiceApi[CoquiTTSSettings, CoquiTTSController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)

    def load_model(self, model: str):
        result = requests.post(
            f'http://{self.address}/load_model',
            json=dict(model=model)
        )
        if result.status_code != 200:
            raise ValueError(f"Error when calling `load_model`\n{result.text}")
        return result.json()

    def dub(self, text: str, model: str|None = None, voice: str|None = None, language: str|None = None):
        reply = requests.post(
            self.endpoint('/dub'),
            json=dict(text=text, model=model, voice=voice, language=language)
        )
        if reply.status_code != 200:
            raise ValueError(f"Error when calling `dub`\n{reply.text}")
        return File(self.current_job_id + '.output.wav', reply.content, File.Kind.Audio)

    def voice_clone(self, text: str, model: str|None = None, voice: str|None = None, language: str|None = None):
        reply = requests.post(
            self.endpoint('/voice_clone'),
            json=dict(text=text, model=model, voice=voice, language=language)
        )
        if reply.status_code != 200:
            raise ValueError(f"Error when calling `voice_clone`\n{reply.text}")
        return File(self.current_job_id + '.output.wav', reply.content, File.Kind.Audio)


    @staticmethod
    def export_model_from_training(
            api: BrainBoxApi,
            source_model_file_path: Path,
            model_name: str):
        target_path = f'custom/{model_name}.pth'
        api.controller_api.upload_resource(
            CoquiTTS,
            target_path,
            source_model_file_path
        )
        api.controller_api.upload_resource(
            CoquiTTS,
            target_path+'.json',
            source_model_file_path.parent/'config.json'
        )
        api.controller_api.upload_resource(
            CoquiTTS,
            target_path+'.speakers.pth',
            source_model_file_path.parent.parent.parent / 'data/speakers.pth'
        )

        return f'custom_models/{model_name}.pth'

    @staticmethod
    def upload_voice(
            api: BrainBoxApi,
            file: Path,
            custom_name: str|None = None
    ):
        if custom_name is None:
            custom_name = file.name
        api.controller_api.upload_resource(
            CoquiTTS,
            f'voices/{custom_name}',
            file
        )

    Controller = CoquiTTSController
    Settings = CoquiTTSSettings

    @classmethod
    def get_ordering_arguments_sequence(cls) -> tuple[str,...]|None:
        return ('model',)
