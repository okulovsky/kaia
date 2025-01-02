import dateutil.parser
import requests
from datetime import datetime
from yo_fluq import FileIO
from pathlib import Path

def get_sample():
    return FileIO.read_json(Path(__file__).parent/'reply.json')

def get_open_meteo(latitude, longitude, timezone):
    reply = requests.get(
        'https://api.open-meteo.com/v1/forecast',
        params=dict(
            latitude=latitude,
            longitude=longitude,
            hourly='temperature_2m,weathercode',
            timezone=timezone
        )
    )
    return reply.json()


def parse_open_meteo(time: datetime, reply):
    for i, t in enumerate(reply['hourly']['time']):
        t = dateutil.parser.parse(t)
        if t>time:
            return {name:reply['hourly'][name][i] for name in ['temperature_2m','weathercode']}





if __name__ == '__main__':
    reply = FileIO.read_json('reply.json')
    print(parse_open_meteo(datetime.now(), reply))
