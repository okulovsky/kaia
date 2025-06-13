"""
### Reusability on the methods' level

Now let's see how we can organize the authorization code better, to be able to reuse it.

First, we can decompose the code to `authorize` and `echobot` methods, and combine the calls in `main`.

"""
from eaglesong.demo.common import *
from eaglesong.demo.example_01_echobot import main as echobot


def authorize(env_variable):
    context = yield ContextRequest()
    user_id = context.user_id

    if env_variable not in os.environ:
        yield Terminate(f'Please add `{env_variable}` environment variable. Your id is {user_id}')
    allowed_user_id = int(os.environ[env_variable])

    if user_id != allowed_user_id:
        raise Terminate(f'User {user_id} is not authorized')


def main():
    yield from authorize('KAIA_TEST_BOT_CHAT_ID')
    yield from echobot()


bot = Bot("auth2", main)


if __name__ == '__main__':
    run(bot)
