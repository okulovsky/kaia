from kaia.kaia.core import Listen
from .internal_intents import NutritionIntents, NutritionReplies
from kaia.avatar.dub.core import Utterance
from ..app.api import Api, RecordRequest, RecordReply
from ..app.database import ReferenceIntake
from dataclasses import dataclass


@dataclass
class FoodConfirmation:
    request: RecordRequest
    reply: RecordReply


class Flow:
    def __init__(self,
                 api: Api,
                 recognition_profile: str,
                 username: str
                 ):
        self.api = api
        self.recognition_profile = recognition_profile
        self.username = username

    def listen_and_recognize(self):
        return Listen().for_free_text().recognize_with(self.recognition_profile)

    def confirm_free_input(self, confirmation_template: str, say_again: str, validator = None, require_yes = False):
        value = yield
        while True:
            if validator is not None and not validator(value):
                yield say_again
                value = yield Listen().for_free_text()
            yield confirmation_template.format(value)
            confirmation = yield self.listen_and_recognize()

            if not require_yes:
                if confirmation.template == NutritionIntents.yes:
                    return value
                else:
                    yield say_again
                    value = yield Listen().for_free_text()
            else:
                if confirmation.template == NutritionIntents.wrong:
                    yield say_again
                    value = yield Listen().for_free_text()
                else:
                    return value

    def input_food_item_by_item(self) -> RecordRequest:
        yield 'What did you eat?'
        yield Listen().for_free_text()
        food = yield from self.confirm_free_input("You've eaten {0}. And how much?", "Say again, what did you eat?")
        amount = yield from self.confirm_free_input('So, {0}. Of which unit?', 'Say again, how much?')
        unit = yield from self.confirm_free_input('Got it, {0}.', 'Say again, of which unit?')
        return RecordRequest(food, amount, unit, self.username)


    def is_numeric(self, value):
        try:
            v = int(value)
            return True
        except:
            pass
        try:
            v = float(value)
            return True
        except:
            pass
        return False


    def question_reference_intake(self, food: str):
        yield f"Seems like it's first time when you eat {food}. How many calories per 100 grams?"
        yield Listen().for_free_text()
        calories = yield from self.confirm_free_input(
            '{0} calories. And how much proteins?',
            'Say again, how many calories?',
            self.is_numeric
        )
        proteins = yield from self.confirm_free_input(
            '{0} grams proteins. And how much fats?',
            'Say again, how much proteins?',
            self.is_numeric
        )
        fats = yield from self.confirm_free_input(
            '{0} grams of fats. And how much carbs?',
            'Say again, how much fats?',
            self.is_numeric
        )
        carbs = yield from self.confirm_free_input(
            '{0} grams of carbs, right?',
            'Say again, how much carbs?',
            self.is_numeric,
            True
        )




    def follow_up_questions(self, request: RecordRequest, reply: RecordReply):
        if reply.unit_not_found:
            raise ValueError("TODO: 1 item or all in whole? Think about it")
            yield f'And how much does in weight in grams?'
            result = yield Listen().for_free_text()
            
        if reply.food_not_found:
            yield from self.question_reference_intake(request.food)




    def confirm_food_item_by_item(self) -> RecordRequest:
        request: RecordRequest = yield from self.input_food_item_by_item()
        reply = self.api.check_record(request)
        if reply.has_follow_up():
            yield from self.follow_up_questions(request, reply)
        return request




    def confirm_food(self):
        food: Utterance = yield None

        if food.template != NutritionIntents.eaten:
            raise ValueError("Something is wrong, `eaten` template is expected")

        record = food.value

        if 'food' not in record:
            yield "Sorry, I didn't get it."
            return self.confirm_food_item_by_item()

        request = RecordRequest(record['food'], record.get('amount', 1), record.get('unit', None), self.username)
        reply = self.api.check_record(request)

        if not reply.has_follow_up():
            yield NutritionReplies.eaten_confirm.utter(**request.__dict__)
            yield "Anything else?"
            user_reply: Utterance = yield self.listen_and_recognize()
            if user_reply.template != NutritionIntents.wrong:
                return request
            fallback = yield from self.confirm_food_item_by_item()
            return fallback

        yield "Did I get it right?"
        yield NutritionReplies.eaten_confirm.utter(**request.__dict__)
        user_reply: Utterance = yield self.listen_and_recognize()
        if user_reply.template != NutritionIntents.yes:
            fallback = yield from self.confirm_food_item_by_item()
            return fallback

        yield from self.follow_up_questions(request, reply)
        return request









