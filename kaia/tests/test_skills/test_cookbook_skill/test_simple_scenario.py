from kaia.skills.cookbook_skill import CookBookSkill, Recipe, CookBookIntents, CookBookReplies
from kaia.skills.notification_skill import NotificationRegister, NotificationInfo, NotificationSkill
from kaia import KaiaAssistant
from eaglesong import Scenario, Automaton
from unittest import TestCase
from avatar.utils import TestTimeFactory
from avatar.daemon import ChatCommand

def S(factory: TestTimeFactory):
    recipe = Recipe.define(
        'tea',
        "Boil water",
        "Put a teabag in the water",
        {1 : "Enjoy your tea"},
        Recipe.Ingredient("teabag"),
        Recipe.Ingredient("water"),
    )
    register = NotificationRegister(
        (ChatCommand('alarm starts'),),
        (ChatCommand('alarm stops'),),
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
            .check(CookBookReplies.next_timer_in(1))
            .act_and_send(lambda: tf.shift(59).event())
            .check()
            .act_and_send(lambda: tf.shift(1).event())
            .check(lambda z: z.text == 'alarm starts')
            .send('Stop')
            .check(lambda z: z.text == 'alarm stops', 'Enjoy your tea', CookBookReplies.all_done())
            .validate()
        )