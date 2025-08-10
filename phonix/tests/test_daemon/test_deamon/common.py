from avatar.messaging import TestStream, AvatarProcessor, IMessage, Confirmation
from avatar.daemon import SoundInjectionCommand, WakeWordEvent, SoundConfirmation, SoundEvent, SoundCommand
from phonix.daemon import *
from unittest import TestCase
from yo_fluq import FileIO
from pathlib import Path
from phonix.tests.test_environment import PhonixTestEnvironmentFactory

PATH = Path(__file__).parent.parent.parent/'files'

def slice(condition):
    def _(q):
        result = []
        for e in q:
            result.append(e)
            if condition(e):
                return result
    return _

