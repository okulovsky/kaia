from kaia.dub.languages.en import *


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

sunny_dict = {
    True: 'sunny',
    False: 'cloudy'
}

today_dict = {
    True: 'today',
    False: 'tomorrow'
}

weather_code_dub = DictDub(weather_code, 'weather_code')

class WeatherIntents(TemplatesCollection):
    question = Template(
        'What is the weather?',
    )
    forecast = Template(
        'Weather forecast'
    )

class WeatherReply(TemplatesCollection):
    weather = Template(
        'It is {temperature_2m} grads today, {weathercode}',
        temperature_2m = CardinalDub(-50, 50),
        weathercode = weather_code_dub
    )

    forecast = Template(
        "The temperature {for_today} is between {min_t} and {max_t}, mostly {is_sunny}, {precipitations}.",
        "The temperature {for_today} is between {min_t} and {max_t}, mostly {is_sunny}, no precipitations.",
        min_t = ToStrDub(),
        max_t = ToStrDub(),
        is_sunny = DictDub(sunny_dict),
        for_today = DictDub(today_dict),
        precipitations = StringListDub()
    )

    precipitation = Template(
        '{code} at {start}',
        '{code} from {start} to {end}',
        code = weather_code_dub,
        start = ToStrDub(),
        end = ToStrDub()
    )

