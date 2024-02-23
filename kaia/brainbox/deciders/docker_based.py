from typing import *
from kaia.infra import subprocess_call
import time
import requests


def initialize(image: str,
               run_arguments,
               sleep_time: Optional[float] = None,
               get_request_to: Optional[str] = None):

    if get_request_to is not None:
        try:
            requests.get(get_request_to, timeout=1)
            return
        except:
            pass


    present = True
    result = subprocess_call(f"docker ps -q --filter ancestor={image}").if_fails("Can't reach docker engine")

    if result.str_output.strip() == '':
        present = False
        containers = (
            subprocess_call(f'docker ps -a -q --filter ancestor={image}')
            .if_fails("Can't get containers list")
        )

        for container in containers.str_output.split('\n'):
            if container.strip() == '':
                continue
            subprocess_call(f'docker stop {container}').if_fails(f"Can't stop container {container}")
            subprocess_call(f'docker rm {container}').if_fails(f"Can't remove container {container}")

        subprocess_call(run_arguments).if_fails("Can't start new container")
        if sleep_time is not None:
            time.sleep(sleep_time)

    if get_request_to is not None:
        try:
            requests.get(get_request_to, timeout=1)
        except:
            raise ValueError(f"Container {image} was {'present' if present else 'newly created'}, but wasn't reacheable at {get_request_to}")





