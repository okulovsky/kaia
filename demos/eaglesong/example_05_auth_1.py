"""
Authorization is very important step of the chat bot. The following code shows the simplest way
to authorize only yourself as a user of the chatbot: you just write your chat id in env. variable,
and check that the user is legit.
"""

from demos.eaglesong.common import *

def main(context: BotContext):
    if 'CHAT_ID' not in os.environ:
        yield Terminate(f'Please add CHAT_ID environment variable. Your id is {context.user_id}')
    chat_id = int(os.environ['CHAT_ID'])
    if context.user_id != chat_id:
        yield Terminate(f'User {context.user_id} is not authorized')

    yield f'Hello. Your user_id is {context.user_id}. Say anything and I will repeat. Or /start to reset.'
    while True:
        yield Listen()
        yield context.input


bot = Bot("auth1", main)

if __name__ == '__main__':
    run(bot)