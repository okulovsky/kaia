import datetime
import re
import time
import requests

class ApiUtils:
    @staticmethod
    def check_address(address):
        if not re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}', address):
            raise ValueError(f'Address must be IP:port, no protocol, no trailing slash, but was:\n{address}')


    @staticmethod
    def wait_for_reply(url, time_in_seconds, endpoint_name=''):
        reply = None
        begin = datetime.datetime.now()
        for i in range(time_in_seconds * 100):
            time.sleep(0.01)
            if i>2 and (datetime.datetime.now()-begin).total_seconds() > time_in_seconds:
                break
            try:
                reply = requests.get(url)
            except:
                continue
            if reply.status_code == 200:
                break
        if reply is None:
            raise ValueError(
                f"Endpoint {endpoint_name} was not reacheable within {time_in_seconds} seconds")
        if reply.status_code != 200:
            raise ValueError(
                f"Endpoint {endpoint_name} was reacheable, but returned bad status code {reply.status_code}\n{reply.text}")


