"""
Authorization is very important step of the chat bot. The following code shows the simplest way
to authorize only yourself as a user of the chatbot: you just write your chat id in env. variable,
and check that the user is legit.
"""

from eaglesong.demo.common import *


def main():
    context = yield ContextRequest()
    user_id = context.user_id

    if 'KAIA_TEST_BOT_CHAT_ID' not in os.environ:
        raise Terminate(f'Please add CHAT_ID environment variable. Your id is {user_id}')
    allowed_user_id = int(os.environ['KAIA_TEST_BOT_CHAT_ID'])

    if user_id != allowed_user_id:
        raise Terminate(f'User {user_id} is not authorized')

    yield f'Say anything and I will repeat. Or /start to reset.'
    while True:
        input = yield Listen()
        yield input



bot = Bot("auth1", main)

if __name__ == '__main__':
    run(bot)