from typing import *
import requests
from kaia.infra import Loc
import subprocess
import threading
import time
from IPython.display import HTML

class Automatic1111Request:
    def __init__(self, url, payload):
        self.url = url
        self.payload = payload
        self.reply = None

    def run(self):
        reply = requests.post(self.url, json=self.payload)
        self.reply = reply.json()



class Automatic1111Dispatcher:
    def __init__(self):
        self.location = Loc.root_folder.parent/'stable-diffusion-webui'
        self.env_name = 'kaia-automatic1111'
        self.python_location = Loc.get_python_by_env(self.env_name)
        self.url = 'http://127.0.0.1:7860'
        self.boot_time_in_seconds = 10


    def run_if_absent(self):
        response = HTML(f'<a href={Automatic1111.url} target=_blank>Open Automatic1111 in browser</a>')
        try:
            requests.get(self.url)
            return response
        except:
            pass

        subprocess.Popen(
            [
                self.python_location,
                self.location/'launch.py',
                '--api'
            ],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=self.location
        )
        for _ in range(self.boot_time_in_seconds):
            try:
                requests.get(self.url)
                return response
            except:
                pass
        raise ValueError("Seems like AUTO1 server has failed to boot up")


    def run_request_sync(self,
                         api,
                         payload):
        rq = Automatic1111Request(self.url + api, payload)
        rq.run()
        return rq.reply


    def run_request(self,
                    api,
                    payload,
                    reporter=None,
                    timeout = 1000,
                    ):
        rq = Automatic1111Request(self.url + api, payload)
        thread = threading.Thread(target=rq.run)
        thread.start()
        for i in range(timeout):
            if rq.reply is not None:
                return rq.reply
            res = requests.get(self.url+'/sdapi/v1/progress')
            try:
                js = res.json()
                prog = js['progress']
                if isinstance(prog, float) or isinstance(prog, int):
                    if reporter is not None:
                        reporter.report_progress(prog)
            except:
                pass
            time.sleep(1)
        return None

Automatic1111 = Automatic1111Dispatcher()










