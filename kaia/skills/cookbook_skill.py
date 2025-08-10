from kaia import IKaiaSkill, ButtonPressedEvent, ButtonGridCommand, World, Listen, Return
from grammatron import *
from .notification_skill import NotificationRegister, NotificationInfo
from dataclasses import dataclass
from yo_fluq import *
from datetime import datetime, timedelta

DISH = VariableDub(
    "dish",
    description="one of the dish in the cookbook"
)

MINUTES = VariableDub(
    "minutes",
    description="the duration of the set timer, in minutes"
)

class CookBookIntents(TemplatesCollection):
    recipe_book = Template("Recipe book")
    recipe = Template(f"How to cook {DISH}")
    next_step = Template("Next step")
    cancel = Template("Cancel the recipe")
    what_to_cook = Template("What do you want to cook?")

class CookBookReplies(TemplatesCollection):
    no_recipe = (
        Template(f"Can't find a recipe for {DISH}")
        .no_paraphrasing()
    )

    too_many_recipies = (
        Template(f"More that one recipe for {DISH}")
        .no_paraphrasing()
    )

    timer_set = (
        Template(f"I'll call you in {PluralAgreement(MINUTES, 'minutes')}")
        .context(f"{World.character} guides {World.user} through recipe, and now it's time to wait. {World.character} sets timer and says {World.character.pronoun} will call {World.user} when the time is right.")
    )

    timer_is_busy = (
        Template(f"You need to wait for the timer. {PluralAgreement(MINUTES, 'minute')} remaining")
        .context(f"{World.user} is asking what is the next step in the recipe, but currently {World.user} needs to wait for the timer to finish the previous step, and {World.character} informs {World.user.pronoun} about this fact.")
    )

    recipe_is_cancelled = (
        Template(f"The recipe is cancelled.")
        .context(reply_to=CookBookIntents.cancel)
    )

@dataclass
class RecipeStage:
    text: str|None = None
    timer_for_minutes: int|None = None

    def __post_init__(self):
        if (self.text is None) == (self.timer_for_minutes is None):
            raise ValueError("Exactly one of `text` and `timer_for_minutes` must be set")

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
        self.notification_register = register
        self.datetime_factory = datetime_factory if datetime_factory is not None else datetime.now

    def get_runner(self):
        return self.run

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.MultiLine

    def get_intents(self) -> Iterable[Template]:
        template = CookBookIntents.recipe.substitute(dish=VariableDub(DISH.name, OptionsDub([r.dish for r in self.recipes])))
        return CookBookIntents.get_templates(template)

    def get_replies(self) -> Iterable[Template]:
        return CookBookReplies.get_templates()

    def get_name(self) -> str:
        return type(self).__name__

    def should_start(self, input) -> bool:
        if isinstance(input, Utterance):
            if input in CookBookIntents.recipe_book or input in CookBookIntents.recipe:
                return True
        return False

    def should_proceed(self, input) -> bool:
        if isinstance(input, Utterance):
            if input in CookBookIntents.next_step:
                return True
            if input in CookBookIntents.cancel:
                return True
        if isinstance(input, CookBookContinuation):
            return True
        if isinstance(input, ButtonPressedEvent):
            return True
        return False

    def run_recipe(self, recipe_name):
        recipies = [r for r in self.recipes if r.dish == recipe_name]
        if len(recipies) == 0:
            yield CookBookReplies.no_recipe(recipe_name)
            raise Return()
        if len(recipies) > 1:
            yield CookBookReplies.too_many_recipies(recipe_name)
            raise Return()
        recipe = recipies[0]
        for stage in recipe.stages:
            if stage.text is not None:
                yield stage.text
            else:
                yield CookBookReplies.timer_set(stage.timer_for_minutes)
                info = NotificationInfo(
                    self.datetime_factory(),
                    timedelta(minutes=stage.timer_for_minutes),
                    CookBookContinuation()
                )
                self.notification_register.instances['cookbook'] = info
                yield
            response = yield Listen()
            if response in CookBookIntents.cancel:
                if 'cookbook' in self.notification_register.instances:
                    del self.notification_register.instances['cookbook']
                yield CookBookReplies.recipe_is_cancelled()
                break

    def run(self):
        input: Utterance = yield
        if input in CookBookIntents.recipe:
            yield from self.run_recipe(input.get_field())
        builder = ButtonGridCommand.Builder(4)
        for recipe in self.recipes:
            builder.add(recipe.dish, dict(dish=recipe.dish))
        builder.add('CANCEL', dict(action='cancel'))
        yield builder.to_overlay()
        button_pressed = yield Listen()
        if not isinstance(button_pressed, ButtonPressedEvent):
            yield CookBookReplies.recipe_is_cancelled()
        if 'action' in button_pressed.button_feedback and button_pressed.button_feedback['action']=='cancel':
            yield CookBookReplies.recipe_is_cancelled()
        yield from self.run_recipe(button_pressed.button_feedback['dish'])










