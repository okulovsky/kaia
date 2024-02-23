from kaia.avatar.dub.languages.en import *


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

weather_code_dub = DictDub(weather_code, 'weather_code')

class WeatherIntents(TemplatesCollection):
    question = Template(
        'What is the weather?',
    )

class WeatherReply(TemplatesCollection):
    weather = Template(
        'It is {temperature_2m} grads today, {weathercode}',
        temperature_2m = CardinalDub(-50, 50),
        weathercode = weather_code_dub
    )

