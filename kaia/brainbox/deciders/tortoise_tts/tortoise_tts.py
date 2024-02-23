import shutil
from typing import *
import sys

from ...core import IDecider
from kaia.infra import Loc
from pathlib import Path
import subprocess
import requests
import time
import atexit
from dataclasses import dataclass

@dataclass
class TortoiseTTSSettings:
    environment = 'tortoise-tts'
    tortoise_tts_path = Loc.root_folder.parent / 'tortoise-tts'
    port = 8091
    test_voice = 'test_voice'
    debug: bool = False
    wait_time_in_seconds: int = 10

    @property
    def python_path(self):
        return Loc.get_python_by_env(self.environment)

    def get_voice_path(self, voice: Optional[str] = None):
        result = self.tortoise_tts_path/'tortoise/voices'
        if voice is not None:
            result /= voice
        return result

class TortoiseTTS(IDecider):
    def __init__(self,
                 settings: TortoiseTTSSettings
                 ):
        self.settings = settings
        self.process = None #type: Optional[subprocess.Popen]
        atexit.register(lambda:self.cooldown(''))


    def warmup(self, parameters: str):
        shutil.copy(
            Path(__file__).parent / 'web_server.py',
            self.settings.tortoise_tts_path/'tortoise/web_server.py'
        )
        process = subprocess.Popen(
            [
                self.settings.python_path,
                self.settings.tortoise_tts_path/'tortoise/web_server.py',
                str(self.settings.port),
                'debug' if self.settings.debug else 'tortoise',
                self.file_cache,
                self.settings.tortoise_tts_path,
            ],
            cwd = self.settings.tortoise_tts_path/'tortoise'
        )
        time.sleep(0.5)
        if process.poll() is not None:
            raise ValueError("Failed to run server, crush on initialization")
        self.process = process

        for _ in range(self.settings.wait_time_in_seconds*10):
            try:
                reply = requests.get(f'http://localhost:{self.settings.port}/status')
                if reply.text=='ok':
                    return
            except:
                # print(traceback.format_exc())
                pass

            time.sleep(0.1)
        raise ValueError('Failed to start server')


    def cooldown(self, parameters: str):
        if self.process is None:
            return
        try:
            requests.post(f'http://localhost:{self.settings.port}/exit')
        except:
            pass
        self.process.terminate()
        for _ in range(self.settings.wait_time_in_seconds*10):
            if self.process.poll() is not None:
                self.process = None
                return
        raise ValueError("Failed to stop the server gracefully")

    def __call__(self, voice: str, text: str, count=3):
        reply = requests.post(f'http://localhost:{self.settings.port}/dub', json=dict(text=text, voice=voice, count=count))
        try:
            result = reply.json()
        except:
            raise ValueError(f"Could not parse content\n{reply.text}")
        if isinstance(result,dict) and '_exception' in result:
            raise ValueError(f"Web server returned exception\n{result['_exception']}")
        return result


    def aligned_dub(self, voice: str, text: str, count=3):
        reply = requests.post(f'http://localhost:{self.settings.port}/aligned_dub', json=dict(text=text, voice=voice, count=count))
        try:
            result = reply.json()
        except:
            raise ValueError(f"Could not parse content\n{reply.text}")
        if isinstance(result,dict) and '_exception' in result:
            raise ValueError(f"Web server returned exception\n{result['_exception']}")
        return result







