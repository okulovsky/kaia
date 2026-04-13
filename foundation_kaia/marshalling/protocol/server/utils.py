import datetime
import time
import requests

class ApiUtils:
    @staticmethod
    def wait_for_reply(url, time_in_seconds, endpoint_name=''):
        reply = None
        if endpoint_name == '':
            endpoint_name = url
        begin = datetime.datetime.now()
        for i in range(time_in_seconds * 100):
            time.sleep(0.01)
            if i > 2 and (datetime.datetime.now() - begin).total_seconds() > time_in_seconds:
                break
            try:
                reply = requests.get(url, timeout=1)
            except Exception:
                continue
            if reply.status_code == 200:
                break
        if reply is None:
            raise ValueError(
                f"Endpoint {endpoint_name} was not reacheable within {time_in_seconds} seconds")
        if reply.status_code != 200:
            raise ValueError(
                f"Endpoint {endpoint_name} was reacheable, but returned bad status code {reply.status_code}\n{reply.text}")

