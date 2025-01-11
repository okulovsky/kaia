import requests
from ....framework import ResourcePrerequisite, DockerWebServiceApi, File, CombinedPrerequisite, ISingleLoadableModelApi
from .controller import CoquiTTSController
from .settings import CoquiTTSSettings
from pathlib import Path

class CoquiTTS(DockerWebServiceApi[CoquiTTSSettings, CoquiTTSController], ISingleLoadableModelApi):
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

    def get_loaded_model(self):
        result =requests.get(
            self.endpoint('/get_loaded_model')
        )
        if result.status_code!=200:
            raise ValueError(f'Error when calling `get_loaded_model`\n{result.text}')
        return result.json()

    def get_loaded_model_name(self) -> str|None:
        model = self.get_loaded_model()
        if model is None:
            return None
        return model['name']

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
    def export_model_from_training(source_model_file_path: Path, model_name: str) -> CombinedPrerequisite:
        target_path = f'custom/{model_name}.pth'
        command = []
        command.append(ResourcePrerequisite(
            CoquiTTS,
            target_path,
            source_model_file_path
        ))
        command.append(ResourcePrerequisite(
            CoquiTTS,
            target_path+'.json',
            source_model_file_path.parent/'config.json'
        ))
        command.append(ResourcePrerequisite(
            CoquiTTS,
            target_path+'.speakers.pth',
            source_model_file_path.parent.parent.parent / 'data/speakers.pth'
        ))
        return CombinedPrerequisite(command)


    @staticmethod
    def upload_voice(file: Path, custom_name: str|None = None) -> ResourcePrerequisite:
        if custom_name is None:
            custom_name = file.name
        return ResourcePrerequisite(
            CoquiTTS,
            f'voices/{custom_name}',
            file
        )

    Controller = CoquiTTSController
    Settings = CoquiTTSSettings

    @classmethod
    def get_ordering_arguments_sequence(cls) -> tuple[str,...]|None:
        return ('model',)
