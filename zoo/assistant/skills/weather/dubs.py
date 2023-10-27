from kaia.persona.dub import DictionaryDub, TemplateDub, EnumDub
from kaia.persona.dub.languages.en import RelativePeriodDub, CardinalDub, DateDub
from yo_fluq_ds import OrderedEnum

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

weather_code_dub = DictionaryDub(weather_code, 'weather_code')

class DayPeriods(OrderedEnum):
    Morning = 0
    Afternoon = 1
    Evening = 2
    Night = 3

class Intents:
    wheather = TemplateDub(
        'What is the weather {period}?',
        'Weather forecast for {period}.',
        period = RelativePeriodDub()
    )

class Replies:
    forecast_first_day = TemplateDub(
        "The forecast for {relative_day}, {date}.",
        relative_day = RelativePeriodDub(),
        date = DateDub(True)
    )

    forecast_following_days = TemplateDub(
        "{relative_day}, {date}.",
        relative_day = RelativePeriodDub(),
        date = DateDub(True)
    )

    day_period = TemplateDub(
        '{period}.',
        period = EnumDub(DayPeriods)
    )

    weather_code = TemplateDub(
        '{wc}.',
        'Mostly {high_wc}, sometimes {wc}.',
        'Mostly {high_wc}, sometimes {wc} or {wc_1}.',
        '{wc} or {wc_1}.',
        '{wc}, {wc_1} or {wc_2}.',
        wc=weather_code_dub,
        high_wc=weather_code_dub,
        wc_1=weather_code_dub,
        wc_2=weather_code_dub
    )

    temperature = TemplateDub(
        'Temperature from {low_temp} grad to {high_temp} grad.',
        low_temp=CardinalDub(-100, 100),
        high_temp=CardinalDub(-100, 100)
    )

    no_forecast = TemplateDub(
        "Nah, I don't know. The forecast is not available for {relative_day}.",
        relative_day = RelativePeriodDub()
    )

    incomplete_forecast = TemplateDub(
        "That's all. The forecast is not available for other days."
    )









