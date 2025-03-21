from typing import Iterable
from ....framework import DockerWebServiceApi, FileLike, File
import requests
from .settings import ZonosSettings
from .controller import ZonosController
import shutil
import os
import numpy as np


class Zonos(DockerWebServiceApi[ZonosSettings, ZonosController]):
    def __init__(self, address: str|None = None):
        super().__init__(address)


    def train(self, speaker: str, samples: Iterable[FileLike.Type]):
        folder = self.controller.resource_folder('voices',speaker)
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder)
        for sample in samples:
            with open(folder/FileLike.get_name(sample), 'wb') as stream:
                with FileLike(sample, self.cache_folder) as data:
                    stream.write(data.read())
        result = requests.post(
            self.endpoint(f'/train/{speaker}')
        )
        if result.status_code!=200:
            raise ValueError(f"Endpoint train returned error\n{result.text}")

    def voiceover(self,
                  text: str,
                  speaker: str,
                  language='en-us',
                  emotion: list[float|int]|np.ndarray|None = None,
                  speaking_rate: int|float|None = None
                  ):
        if emotion is not None:
            emotion = [float(z) for z in emotion]
        dct = dict(
            text=text,
            speaker=speaker,
            language=language,
            emotion = emotion,
            speaking_rate=speaking_rate
        )
        result = requests.post(
            self.endpoint('/voiceover'),
            json = dct
        )
        if result.status_code!=200:
            raise ValueError(f"Endpoint voiceover returned error\n{result.text}")
        return File(
            self.current_job_id+'.output.wav',
            result.content
        )


    Settings = ZonosSettings
    Controller = ZonosController

    class Emotions:
        Happiness = np.array([1, 0, 0, 0, 0, 0, 0, 0])
        Sadness =   np.array([0, 1, 0, 0, 0, 0, 0, 0])
        Disgust =   np.array([0, 0, 1, 0, 0, 0, 0, 0])
        Fear =      np.array([0, 0, 0, 1, 0, 0, 0, 0])
        Surprise =  np.array([0, 0, 0, 0, 1, 0, 0, 0])
        Anger =     np.array([0, 0, 0, 0, 0, 1, 0, 0])
        Other =     np.array([0, 0, 0, 0, 0, 0, 1, 0])
        Neutral =   np.array([0, 0, 0, 0, 0, 0, 0, 1])

