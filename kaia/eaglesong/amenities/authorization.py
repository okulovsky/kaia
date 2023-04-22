from ..core import Routine, BotContext, Terminate
import os

class Authorization(Routine):
    def __init__(self, inner = None, env_name='CHAT_ID'):
        self.inner = inner
        self.env_name = env_name

    def run(self, c: BotContext):
        if self.env_name not in os.environ:
            yield Terminate(f'Please add {self.env_name} environment variable. Your id is {c.user_id}')
        chat_id = int(os.environ[self.env_name])
        if c.user_id!=chat_id:
            yield Terminate(f'User {c.user_id} is not authorized')
        if self.inner is not None:
            yield Routine.ensure(self.inner)
