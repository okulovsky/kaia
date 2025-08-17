from kaia.skills.cookbook_skill import CookBookSkill, Recipe, CookBookIntents
from kaia.skills.notification_skill import NotificationRegister, NotificationInfo, NotificationSkill
from kaia import KaiaAssistant
from grammatron import Utterance
from eaglesong import Scenario, Automaton
from unittest import TestCase
from avatar.utils import TestTimeFactory

def S(factory: TestTimeFactory):
    recipe = Recipe(
        'tea',
        [
            Recipe.Stage("Boil water"),
            Recipe.Stage("Put a teabag in the water"),
            Recipe.Stage(timer_for_minutes=1),
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
            CookBookSkill(register, [recipe], factory),

        ],
        raise_exception=True
    )
    return Scenario(lambda: Automaton(assistant, None))


class CookbookSkillTestCase(TestCase):
    def test_cookbook(self):
        tf = TestTimeFactory()
        (
            S(tf)
            .send(CookBookIntents.recipe('tea'))
            .check(str)
            .send(CookBookIntents.next_step())
            .check(str)
            .send(CookBookIntents.next_step())
            .check(Utterance)
            .act_and_send(lambda: tf.shift(59).event())
            .check()
            .act_and_send(lambda: tf.shift(1).event())
            .check('alarm starts')
            .send('Stop')
            .check('alarm stops', 'Enjoy your tea')
            .validate()
        )