from kaia.skills.cookbook_skill import CookBookSkill, Recipe, CookBookIntents
from kaia.skills.notification_skill import NotificationRegister, NotificationInfo, NotificationSkill
from kaia.kaia import KaiaAssistant, TestTimeFactory
from eaglesong import Scenario, Automaton
from unittest import TestCase

def S(factory: TestTimeFactory):
    recipe = Recipe(
        'tea',
        [
            Recipe.Stage("Boil water"),
            Recipe.Stage("Put a teabag in the water, and wait 1 minute", 1),
            Recipe.Stage("Enjoy your tea"),
        ]
    )
    register = NotificationRegister(
        ('alarm starts',),
        ('alarm stops',),
    )

    assistant = KaiaAssistant(
        [
            NotificationSkill([register], 1,),
            CookBookSkill(register, [recipe], factory)
        ]
    )
    return Scenario(lambda: Automaton(assistant, None))


class CookbookTestCase(TestCase):
    def test_cookbook(self):
        tf = TestTimeFactory()
        (
            S(tf)
            .send(CookBookIntents.recipe('tea'))
            .check(str)
            .send(CookBookIntents.next_step())
            .check(str)
            .act_and_send(lambda: tf.shift(59).tick())
            .check()
            .act_and_send(lambda: tf.shift(1).tick())
            .check('alarm starts')
            .send('Stop')
            .check('alarm stops', 'Enjoy your tea')
            .validate()
        )