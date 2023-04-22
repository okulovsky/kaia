"""
Another way of passing data between functions is simply storing them in the fields of the object.
It is natural to inherit such object from `Routine`. If you pass this object to chatbot,
the bot will understand that you want to run its `run`.

However, this object will be shared between all the users of your chatbot. To avoid confusion,
the new copy of such `Routine` object must be created for each customer. This is why we
supply `Bot` class with `factory=Questionnaire` instead of `function=Questionnaire().main`.
"""

from demos.eaglesong.common import *

class Questionnaire(Routine):
    def run_questionnaire(self, context):
        yield 'What is your name?'
        yield Listen()
        self.name = context.input

        yield f'Where are you from, {self.name}?'
        yield Listen()
        self.country = context.input

    def run(self, context):
        yield Subroutine(self.run_questionnaire)
        yield f"Nice to meet you, {self.name} from {self.country}!"


bot = Bot("quest3", factory=Questionnaire) # NOT Bot(Questionnaire().main)


if __name__ == '__main__':
    run(bot)
