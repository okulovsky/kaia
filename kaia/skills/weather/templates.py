from eaglesong.templates import *
from dataclasses import dataclass


# https://open-meteo.com/en/docs#hourly=temperature_2m,weathercode
weather_code = {
    0: 'clear sky',
    1: 'mainly clear',
    2: 'partly cloudy',
    3: 'very cloudy',
    45: 'fog',
    48: 'freezing fog',
    51: 'light drizzle',
    53: 'moderate drizzle',
    55: 'dense drizzle',
    56: 'light freezing drizzle',
    57: 'dense freezing drizzle',
    61: 'slight rain',
    63: 'moderate rain',
    65: 'heavy rain',
    66: 'light freezing rain',
    67: 'heavy freezing rain',
    71: 'slight snowfall',
    73: 'moderate snowfall',
    75: 'heavy snowfall',
    77: 'snow grains',
    80: 'slight rain showers',
    81: 'moderate rain showers',
    82: 'violent rain showers',
    85: 'slight snow showers',
    86: 'heavy snow showers',
    95: 'thunderstorm',
    96: 'thunderstorm with slight hail',
    99: 'thunderstorm with heavy hail'
}

inverted_weather_code = {s:v for v, s in weather_code.items()}

sunny_dict = {
    'sunny': True,
    'cloudy': False
}

today_dict = {
    'today': True,
    'tomorrow': False,
}

class WeatherIntents(TemplatesCollection):
    question = Template(
        'What is the weather?',
    )
    forecast = Template(
        'Weather forecast'
    )

TEMPERATURE = TemplateVariable(
    'temperature',
    ToStrDub(),
    "Temperature, from -50 to 50 Celsius"
)

MIN_TEMPERATURE = TEMPERATURE.rename("min_t")
MAX_TEMPERATURE = TEMPERATURE.rename("max_t")

WEATHER_CODE = TemplateVariable(
    'weather_code',
    OptionsDub(inverted_weather_code),
    "Weather code, can be e.g. `clear sky`, `cloudy`, `rain` or `blizzard`"
)

TODAY = TemplateVariable(
    "for_today",
    OptionsDub(today_dict),
    "Word `today` or `tomorrow`"
)

SUNNY = TemplateVariable(
    'is_sunny',
    OptionsDub(sunny_dict),
    "Word `sunny` or `cloudy`"
)

TIME_START = TemplateVariable(
    "start",
)

TIME_END = TemplateVariable(
    "end"
)


@dataclass
class Precipitation:
    weather_code: int
    start: int
    end: int|None = None

@dataclass
class Forecast:
    for_today: bool
    min_t: int
    max_t: int
    is_sunny: bool
    precipitations: tuple[Precipitation,...]


precipitation_template = DataclassTemplateDub(
    Precipitation,
    f'{WEATHER_CODE} at {TIME_START}',
    f'{WEATHER_CODE} from {TIME_START} to {TIME_END}',
)

PRECIPITATIONS = TemplateVariable(
    'precipitations',
    ListDub(precipitation_template, word_if_empty='no precipitations'),
    "the string describing the precipitations during the day, e.g. `rain at 16:00, drizzle from 17:00 to 19:00`"
)



class WeatherReply(TemplatesCollection):
    weather = Template(
        f'It is {TEMPERATURE} grads today, {WEATHER_CODE}',
    )

    forecast = Template(
        f"The temperature {TODAY} is between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}, mostly {SUNNY}, {PRECIPITATIONS}.",
    ).with_type(Forecast)



