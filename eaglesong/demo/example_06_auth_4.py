"""
### Providing the chatflow as inner routine

Finally, let's get of this `main` method, so we could compose our skill from `Authorize` object and
`echobot` function like from bricks. To do so, we pass `echobot` function to `Authorize`, and
`Authorize` will call it when ready.

There is one non-trivial moment about this bot. In previous cases, we run `main` method, and inside
this method, created `Authorize` object (and potentially lots of other objects). For each new user of the chat bot,
its individual `main` call was created, and individual copies of all other objects.

**By default, it's not the case now**. If you create bot as in the commented line below, there will be one object
for all the users of the chatbot, and all of them will share its fields values!

Sometimes it's a desirable behaviour. But often enough we want to avoid it, use the `lambda` syntax as below.
"""
from eaglesong.demo.common import *
from eaglesong.demo.example_01_echobot import main as echobot

class Authorize:
    def __init__(self, env_variable, inner_routine):
        self.env_variable = env_variable
        self.inner_routine = inner_routine

    def __call__(self):
        context = yield ContextRequest()
        user_id = context.user_id

        if self.env_variable not in os.environ:
            yield Terminate(f'Please add `{self.env_variable}` environment variable. Your id is {user_id}')
        allowed_user_id = int(os.environ[self.env_variable])

        if user_id != allowed_user_id:
            raise Terminate(f'User {user_id} is not authorized')

        yield from self.inner_routine()

"""
INCORRECT way to create a bot would be:
`bot = Bot("auth2", Authorize('KAIA_TEST_BOT_CHAT_ID', echobot))`

It can be fixed with deepcopy, but that is sometimes desired behaviour, so factory is better

The correct way is:
"""

bot = Bot("auth2", lambda: Authorize('KAIA_TEST_BOT_CHAT_ID', echobot)())

if __name__ == '__main__':
    run(bot)
