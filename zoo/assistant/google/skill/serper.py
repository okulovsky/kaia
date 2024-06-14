import http.client
import json
import os

from kaia.infra import Loc, FileIO

def call_serper(
        api_key: str,
        query: str,
        location: str = 'Berlin, Germany',
        gl: str = 'de'
):
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({
        "q": query,
        "location": location,
        "gl": gl
    })
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))


if __name__ == '__main__':
    result = call_serper(os.environ['SERPER_API_KEY'],'How long to boil an egg')
    FileIO.write_json(result, 'example_response.json')

