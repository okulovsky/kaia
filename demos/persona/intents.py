from kaia.persona.dub.core import Template, TemplatesCollection
from kaia.persona.dub.languages.en import TimedeltaDub, OrdinalDub, EnumDub
from enum import Enum

class WheatherDays(Enum):
    Today = 1
    Tomorrow = 2

class TimeOfDay(Enum):
    Morning = 1
    Afternoon = 2
    Evening = 3
    Night = 4

class Transport(Enum):
    Bus = 0
    Train = 1
    Tram = 2

class Dishes(Enum):
    Borsch = 0
    BeefStroganoff = 'Beef-Stroganoff'
    Cheesecake = 2
    Porrige = 3
    Ooha = 4 

class Intents(TemplatesCollection):
    yes = Template(
        'Yes',
        'Sure',
        'Go on'
    )

    no = Template(
        'No.',
        'Stop!',
        'Cancel!'
    )

    weather = Template(
        'What is the weather {day}?',
        'What is the weather {time}?',
        'What is the weather {day} {time}?',
        day = EnumDub(WheatherDays),
        time = EnumDub(TimeOfDay)
    )

    time = Template(
        'What time is it?'
    )

    date = Template(
        'What date is it?'
    )

    transport = Template(
        'When the {transport} departs?',
        transport = EnumDub(Transport)
    )

    timer_create = Template(
        'Set the timer for {duration}',
        'Set the {number} timer for {duration}',
        duration = TimedeltaDub(),
        number = OrdinalDub(1, 10)
        )

    timer_how_much_time = Template(
        'How much time left?'
    )

    timer_how_many_timers = Template(
        "How many timers do I have?"
    )

    timer_cancel = Template(
        'Cancel the timer',
        'Cancel the {number} timer',
        number = OrdinalDub(1, 10)
    )

    spotify = Template(
        'Play music',
        'Play spotify'
    )

    cook = Template(
        'Let us cook some {dish}!',
        'How to cook {dish}?',
        'I want to cook {dish}',
        dish = EnumDub(Dishes)
    )













