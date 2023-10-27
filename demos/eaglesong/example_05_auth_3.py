"""
The decomposition to functions is totally fine. But myself, I prefer the object-oriented way of encoding skills.
Here, we first create `Authorize` object. Then, we may do some fine-tuning of this object (sometimes
skills have lots of internal variables and it's unhandy to place all of them in constructor). And finally,
we use this object like a function in `yield from`.

Essentially, we write something like `yield from Authorize('KAIA_TEST_BOT_CHAT_ID')().
Those double brackets may seem weird, but this is totally fine thanks to `Authorize` class
implementing `__call__` method.
"""
from demos.eaglesong.common import *
from demos.eaglesong.example_01_echobot import main as echobot

class Authorize:
    def __init__(self, env_variable):
        self.env_variable = env_variable

    def __call__(self):
        context = yield ContextRequest()
        user_id = context.user_id

        if self.env_variable not in os.environ:
            yield Terminate(f'Please add `{self.env_variable}` environment variable. Your id is {user_id}')
        allowed_user_id = int(os.environ[self.env_variable])

        if user_id != allowed_user_id:
            raise Terminate(f'User {user_id} is not authorized')


def main():
    authorize = Authorize('KAIA_TEST_BOT_CHAT_ID')
    # Here some fine-tuning of `authorize` object can take place
    yield from authorize()
    yield from echobot()


bot = Bot("auth2", main)


if __name__ == '__main__':
    run(bot)
