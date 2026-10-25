from grammatron import Template, TemplatesCollection, VariableDub, OptionsDub, OrdinalDub, CardinalDub

ROOM = VariableDub(
    'room',
    OptionsDub(['kitchen', 'bedroom', 'bathroom', 'living room']),
    'the room where the light is turned on',
)

INDEX = VariableDub(
    'index',
    OrdinalDub(1, 10),
    'when several alarms are ringing, the index of the alarm, so `first`, `second`, etc up to `tenth`.',
)

PERSON = VariableDub(
    'person',
    OptionsDub(['Haruto', 'Yuki', 'Sakura', 'Ren', 'Aoi']),
    'the name of the person to call',
)

MINUTES = VariableDub(
    'minutes',
    CardinalDub(1, 60),
    'in how many minutes to remind',
)


class TestbedIntents(TemplatesCollection):
    """
    Neutral intents to test the NLU on, one for each kind of template the skills have:
    without variables, with an optional variable, with options that are names in a foreign language, with a number.
    """
    weather = Template("What's the weather like?")
    good_night = Template('Good night')
    play_music = Template('Play some music')
    light = Template('Turn on the light', f'Turn on the light in the {ROOM}')
    stop_alarm = Template('Stop the alarm', f'Stop the {INDEX} alarm')
    call = Template(f'Call {PERSON}')
    remind = Template(f'Remind me in {MINUTES} minutes')
