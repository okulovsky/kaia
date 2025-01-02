from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
from .templates import WeatherReply
from .settings import WeatherSettings



@dataclass
class Precipitation:
    code: int
    start: int
    end: int|None = None

@dataclass 
class Forecast:
    for_today: bool
    min_t: int
    max_t: int
    is_sunny: bool
    precipitations: tuple[Precipitation,...]|None



def _get_precipitation(df):
    buffer = []
    
    for time,code in zip(df.hour, df.weathercode):
        if len(buffer)==0 or code!=buffer[-1]['code']:
            buffer.append(dict(code=code, start=time, end = time))
        else:
            buffer[-1]['end'] = time
    
    
    pres = []
    for b in buffer:
        if b['code']<=3:
            continue
        elif b['start'] == b['end']:
            pres.append(Precipitation(b['code'], b['start']))
        else:
            pres.append(Precipitation(b['code'], b['start'], b['end']))

    if len(pres)==0:
        return None
    return pres
    

def make_forecast(data, dt: datetime, settings: WeatherSettings):
    df = pd.DataFrame(data['hourly'])
    if dt.hour>settings.forecast_for_next_day_from_hour:
        for_today = False
        date = dt.date()+timedelta(days=1)
        start_time = settings.forecast_from_hour
    else:
        for_today = True
        date = dt.date()
        start_time = dt.hour

    df.time = pd.to_datetime(df.time)

    df = df.loc[df.time.dt.date==date]

    df['hour'] = df.time.dt.hour
    df = df.loc[(df.hour >= start_time) & (df.hour <= settings.forecast_to_hour)]

    df['is_sunny'] = df.weathercode.isin([1,2])

    max_temperature = int(df.temperature_2m.max())
    min_temperature = int(df.temperature_2m.min())
    is_sunny = df.is_sunny.mean() > 0.5

    ps = _get_precipitation(df)
    return Forecast(for_today, min_temperature, max_temperature, is_sunny, ps)

    
def convert_forecast_to_utterance(forecast: Forecast):
    value = forecast.__dict__
    if value['precipitations'] is not None:
        value['precipitations'] = tuple(WeatherReply.precipitation.to_str(s.__dict__) for s in value['precipitations'])
    return WeatherReply.forecast.utter(**value)


