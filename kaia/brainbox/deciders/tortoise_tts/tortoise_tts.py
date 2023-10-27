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
import traceback



class TortoiseTTS(IDecider):
    def __init__(self,
                 python_path: Path,
                 tortoise_path: Path,
                 wait_time_in_seconds = 10,
                 port = '8087',
                 debug = False
                 ):
        self.process = None #type: Optional[subprocess.Popen]
        self.python_path = python_path
        self.tortoise_path = tortoise_path
        self.wait_time_in_seconds = wait_time_in_seconds
        self.port = port
        self.debug = debug
        atexit.register(self.cooldown)


    def warmup(self):
        shutil.copy(
            Path(__file__).parent / 'web_server.py',
            self.tortoise_path/'tortoise/web_server.py'
        )
        process = subprocess.Popen(
            [
                self.python_path,
                self.tortoise_path/'tortoise/web_server.py',
                str(self.port),
                'debug' if self.debug else 'tortoise',
                self.file_cache,
                self.tortoise_path,
            ],
            cwd = self.tortoise_path/'tortoise'
        )
        time.sleep(0.5)
        if process.poll() is not None:
            raise ValueError("Failed to web server, crush on initialization")
        self.process = process

        for _ in range(self.wait_time_in_seconds*10):
            try:
                reply = requests.get(f'http://localhost:{self.port}/status')
                if reply.text=='ok':
                    return
            except:
                # print(traceback.format_exc())
                pass

            time.sleep(0.1)
        raise ValueError('Failed to start server')


    def cooldown(self):
        if self.process is None:
            return
        try:
            requests.post(f'http://localhost:{self.port}/exit')
        except:
            pass
        self.process.terminate()
        for _ in range(self.wait_time_in_seconds*10):
            if self.process.poll() is not None:
                self.process = None
                return
        raise ValueError("Failed to stop the server gracefully")

    def dub(self, voice: str, text: str):
        reply = requests.post(f'http://localhost:{self.port}/dub', json=dict(text=text, voice=voice))
        try:
            result = reply.json()
        except:
            raise ValueError(f"Could not parse content\n{reply.text}")
        if isinstance(result,dict) and '_exception' in result:
            raise ValueError(f"Web server returned exception\n{result['_exception']}")
        return result


    def aligned_dub(self, voice: str, text: str):
        reply = requests.post(f'http://localhost:{self.port}/aligned_dub', json=dict(text=text, voice=voice))
        try:
            result = reply.json()
        except:
            raise ValueError(f"Could not parse content\n{reply.text}")
        if isinstance(result,dict) and '_exception' in result:
            raise ValueError(f"Web server returned exception\n{result['_exception']}")
        return result







