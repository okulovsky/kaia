from kaia.skills.cookbook_skill import CookBookSkill, Recipe, CookBookIntents, CookBookReplies
from kaia.skills.notification_skill import NotificationRegister, NotificationInfo, NotificationSkill
from kaia import KaiaAssistant
from eaglesong import Scenario, Automaton
from unittest import TestCase
from avatar.utils import TestTimeFactory
from avatar.daemon import ChatCommand

def S(factory: TestTimeFactory):
    recipe = Recipe(
        'tea',
        (
            Recipe.Step("Stage1"),
            Recipe.Step("Stage2")
        ),
        (
        )
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
            .check('Stage1')
            .send(CookBookIntents.next_step())
            .check('Stage2')
            .send(CookBookIntents.next_step())
            .check(CookBookReplies.all_done())
            .validate()
        )