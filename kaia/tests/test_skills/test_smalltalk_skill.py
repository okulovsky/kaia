from grammatron import Template, TemplatesCollection
from unittest import TestCase
from kaia.skills import SmalltalkSkill
from eaglesong import Automaton, Scenario
from kaia import KaiaAssistant

class Intents(TemplatesCollection):
    how_are_how = Template("How are you?")
    whats_up = Template("What's up?")

class Replies(TemplatesCollection):
    i_am_fine = Template("I'm fine").context(reply_to=Intents.how_are_how)
    not_much = Template("Not much").context(reply_to=Intents.whats_up)

def create_automaton():
    skills = [SmalltalkSkill(Intents, Replies)]
    assistant = KaiaAssistant(skills)
    help.assistant = assistant
    return Automaton(assistant, None)

class SmalltalkTestCase(TestCase):
    def test_smalltalk(self):
        (
            Scenario(create_automaton)
            .send(Intents.whats_up())
            .check(Replies.not_much())
            .send(Intents.how_are_how())
            .check(Replies.i_am_fine())
            .validate()
        )