from typing import Optional, Callable
from kaia import KaiaSkillBase, ButtonPressedEvent, ButtonGridCommand, World, Listen, Return
from grammatron import *
from ..notification_skill import NotificationRegister, NotificationInfo
from dataclasses import dataclass
from datetime import datetime, timedelta
from ...assistant import CommonIntents
from .recipe import Recipe
from .intents import CookBookIntents, CookBookReplies
from uuid import uuid4


@dataclass
class CookBookContinuation:
    reminder: Recipe.Reminder



class CookBookSkill(KaiaSkillBase):
    def __init__(self,
                 register: NotificationRegister,
                 recipes: list[Recipe],
                 datetime_factory: Optional[Callable[[], datetime]] = None,
                 ingredients_callback: Optional[Callable[[Recipe], None]] = None,
                 ingredients_confirmation: Optional[Template] = None
                 ):
        self.recipes = recipes
        self.notification_register = register
        self.datetime_factory = datetime_factory if datetime_factory is not None else datetime.now
        self.ingredients_callback = ingredients_callback
        self.ingredients_confirmation = ingredients_confirmation
        recipe_intent = CookBookIntents.recipe.substitute(
            dish=OptionsDub([r.dish for r in self.recipes])
        )
        ingredient_intent = CookBookIntents.ingredients.substitute(
            dish=OptionsDub([r.dish for r in self.recipes])
        )
        super().__init__(
            CookBookIntents.get_templates(recipe_intent, ingredient_intent),
            CookBookReplies,
        )
        self.current_recipe: Recipe|None = None
        self.current_recipe_stage: int|None = None



    def should_start(self, input) -> bool:
        if isinstance(input, Utterance):
            if input in CookBookIntents.recipe_book or input in CookBookIntents.recipe or input in CookBookIntents.recipe_book:
                return True
        return False

    def should_proceed(self, input) -> bool:
        if isinstance(input, Utterance):
            for intent in CookBookIntents.get_templates():
                if input in intent:
                    return True
        if isinstance(input, CookBookContinuation):
            return True
        if isinstance(input, ButtonPressedEvent):
            fb = input.button_feedback
            if not isinstance(fb, dict):
                return False
            if 'origin' not in fb:
                return False
            if fb['origin'] != 'cookbook':
                return False
            return True
        return False

    def run(self):
        while True:
            print(f"TIME {self.datetime_factory()}")
            input = yield
            if isinstance(input, Utterance):
                if input in CookBookIntents.recipe:
                    dish = input.get_field()
                    yield from self._chat_recipe(dish)
                elif input in CookBookIntents.recipe_book:
                    yield from self._chat_recipe_book()
                elif input in CookBookIntents.next_step:
                    yield from self._chat_step()
                elif input in CookBookIntents.cancel:
                    yield from self._chat_remove_everything()
                    return
                elif input in CookBookIntents.ingredients:
                    yield from self._chat_ingredients(input.get_field())
                else:
                    raise ValueError("Should not be here")
            elif isinstance(input, ButtonPressedEvent):
                yield ButtonGridCommand.empty()
                if not input.button_feedback['cancel']:
                    yield from self._chat_recipe(input.button_feedback['dish'])
            elif isinstance(input, CookBookContinuation):
                yield input.reminder.announcement
                yield from self._chat_timer_or_end()

            else:
                raise ValueError("Should not be here")

            if self.current_recipe is None and self._get_next_relevant_timer() is None:
                break

            yield Listen()



    def _chat_timer_or_end(self):
        next_timer = self._get_next_relevant_timer()
        if next_timer is not None:
            duration = (next_timer.end - self.datetime_factory()).total_seconds()
            duration = int(duration / 60)
            yield CookBookReplies.next_timer_in(duration)
        else:
            yield CookBookReplies.all_done()

    def _chat_step(self):
        if self.current_recipe is not None:
            if self.current_recipe_stage >= 0 and self.current_recipe_stage < len(self.current_recipe.steps):
                last_step = self.current_recipe.steps[self.current_recipe_stage]
                for reminder in last_step.reminders:
                    self.notification_register.instances.append(NotificationInfo(
                        self.datetime_factory(),
                        timedelta(minutes=reminder.delay_in_minutes),
                        CookBookContinuation(reminder),
                        dict(skill='cookbook', dish=self.current_recipe.dish),
                        reminder.label
                    ))

            self.current_recipe_stage += 1

            if self.current_recipe_stage>=0 and self.current_recipe_stage < len(self.current_recipe.steps):
                step: Recipe.Step = self.current_recipe.steps[self.current_recipe_stage]
                yield step.main_text
            else:
                self.current_recipe = None
                self.current_recipe_stage = None
                yield from self._chat_timer_or_end()
        else:
            yield from self._chat_timer_or_end()



    def _chat_get_single_recipe(self, dish: str):
        yield
        recipe_candidates = [r for r in self.recipes if r.dish == dish]
        if len(recipe_candidates) == 0:
            yield CookBookReplies.no_recipe()
            return None
        elif len(recipe_candidates) > 1:
            raise ValueError(f"Duplicating dish {dish}")
        return recipe_candidates[0]


    def _chat_recipe(self, dish: str):
        recipe = yield from self._chat_get_single_recipe(dish)
        if recipe is not None:
            if self.current_recipe is not None:
                yield CookBookReplies.busy(self.current_recipe.dish)
            else:
                self.current_recipe = recipe
                self.current_recipe_stage = -1
                yield from self._chat_step()
        else:
            yield CookBookReplies.no_recipe()


    def _chat_recipe_book(self):
        if self.current_recipe is not None:
            yield CookBookReplies.busy(self.current_recipe.dish)
        else:
            builder = ButtonGridCommand.Builder(4)
            for recipe in self.recipes:
                builder.add(recipe.dish, dict(origin='cookbook', dish=recipe.dish, cancel=False))
            builder.add('CANCEL', dict(origin='cookbook', dish=None, cancel=True))
            yield builder.to_grid()
            yield CookBookReplies.pick_recipe()

    def _chat_remove_everything(self):
        for i in range(len(self.notification_register.instances)-1,-1, -1):
            tags = self.notification_register.instances[i].tags
            if tags.get('skill', '') == 'cookbook':
                del self.notification_register.instances[i]
        self.current_recipe_stage = None
        self.current_recipe = None
        yield CookBookReplies.recipe_is_cancelled()

    def _chat_ingredients(self, dish: str):
        recipe = yield from self._chat_get_single_recipe(dish)
        if recipe is None:
            yield CookBookReplies.no_recipe()
        elif recipe.ingredients is None:
            yield CookBookReplies.no_ingredients(dish)
        else:
            if self.ingredients_callback is not None:
                self.ingredients_callback(recipe)
                if self.ingredients_confirmation is not None:
                    yield self.ingredients_confirmation
            else:
                text = [f"Ingredients for {dish}", ""]
                template = Recipe.Ingredient.template()
                for i in recipe.ingredients:
                    text.append(template.to_str(i, DubParameters(spoken=False)))
                yield "\n".join(text)




    def _get_next_relevant_timer(self) -> NotificationInfo|None:
        nearest_end: datetime|None = None
        nearest: NotificationInfo|None = None
        for instance in self.notification_register.instances:
            if instance.tags.get('skill', '') != 'cookbook':
                continue
            if nearest_end is None or instance.end < nearest_end:
                nearest_end = instance.end
                nearest = instance
        return nearest



















