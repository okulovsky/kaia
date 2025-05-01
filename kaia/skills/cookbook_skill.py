from typing import Iterable
from kaia.kaia import IKaiaSkill
from kaia.dub import Template, TemplatesCollection, ToStrDub, StringSetDub, Utterance
from kaia.dub.languages.en import CardinalDub
from .notification_skill import NotificationRegister, NotificationInfo
from dataclasses import dataclass
from yo_fluq import *
from datetime import datetime, timedelta
from eaglesong import Listen, Return

class CookBookIntents(TemplatesCollection):
    recipe = Template(
        "How to cook {dish}",
        dish=ToStrDub()
    )

    next_step = Template(
        "Next step"
    )

class CookBookReplies(TemplatesCollection):
    no_recipe = Template(
        "Can't find a recipe for {dish}",
        dish = ToStrDub()
    )
    too_many_recipies = Template(
        "More that one recipe for {dish}",
        dish = ToStrDub()
    )
    timer_set = Template(
        "I'll call you in {minutes} minutes",
        minutes = CardinalDub(1000)
    )

@dataclass
class RecipeStage:
    text: str
    timer_for_minutes: int|None = None



@dataclass
class Recipe:
    dish: str
    stages: list[RecipeStage]
    Stage = RecipeStage


@dataclass
class CookBookContinuation:
    pass

class CookBookSkill(IKaiaSkill):
    def __init__(self,
                 register: NotificationRegister,
                 recipes: list[Recipe],
                 datetime_factory: Optional[Callable[[], datetime]] = None):
        self.recipes = recipes
        dub = StringSetDub([r.dish for r in recipes])
        self.template = CookBookIntents.recipe.substitute(dict(dish=dub))
        self.notification_register = register
        self.datetime_factory = datetime_factory if datetime_factory is not None else datetime.now

    def get_runner(self):
        return self.run

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.MultiLine

    def get_intents(self) -> Iterable[Template]:
        return [self.template, CookBookIntents.next_step]

    def get_replies(self) -> Iterable[Template]:
        return CookBookReplies.get_templates()

    def get_name(self) -> str:
        return type(self).__name__

    def should_start(self, input) -> bool:
        return isinstance(input, Utterance) and input in self.template

    def should_proceed(self, input) -> bool:
        if isinstance(input, Utterance) and input in CookBookIntents.next_step:
            return True
        if isinstance(input, CookBookContinuation):
            return True
        return False

    def run(self):
        input: Utterance = yield
        recipe_name = input.get_field()
        recipies = [r for r in self.recipes if r.dish == recipe_name]
        if len(recipies) == 0:
            yield CookBookReplies.no_recipe(recipe_name)
            raise Return()
        if len(recipies) > 1:
            yield CookBookReplies.too_many_recipies(recipe_name)
            raise Return()
        recipe = recipies[0]
        for stage in recipe.stages:
            yield stage.text
            if stage.timer_for_minutes is not None:
                info = NotificationInfo(
                    self.datetime_factory(),
                    timedelta(minutes=stage.timer_for_minutes),
                    CookBookContinuation()
                )
                self.notification_register.instances['cookbook'] = info
                yield
            yield Listen()





