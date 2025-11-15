from ....framework import DockerWebServiceApi, FileLike, File
import requests
from .settings import ChatterboxSettings
from .controller import ChatterboxController



class Chatterbox(DockerWebServiceApi[ChatterboxSettings, ChatterboxController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)


    def train(self, speaker: str, sample_file: FileLike.Type):
        with FileLike(sample_file, self.cache_folder) as content:
            reply = requests.post(
                self.endpoint('/train/'+speaker),
                files=(
                    (FileLike.get_name(sample_file), content),
                )
            )
            if reply.status_code != 200:
                raise ValueError(f"Endpoint returned error \n{reply.text}")
            return reply.text
        
    def voiceover(self, text: str, speaker: str, language: str = 'en'):
        reply = requests.post(
            self.endpoint('/voiceover'),
            json=dict(
                text=text,
                speaker=speaker,
                language=language
            )
        )
        if reply.status_code != 200:
            raise ValueError(f"Endpoint returned error \n{reply.text}")
        return File(
            self.current_job_id+'.output.wav',
            reply.content,
            File.Kind.Audio
        )

    Settings = ChatterboxSettings
    Controller = ChatterboxController
