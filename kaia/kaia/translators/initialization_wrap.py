from typing import *
from kaia.eaglesong.core import Listen, Automaton, ContextRequest
from ..core import Start

class InitializationWrap:
    def __init__(self,
                 inner_function,
                 start_commands: List,
                 first_time_commands: Optional[List] = None,
                 supress_output: bool = False
                 ):
        self.inner_function = inner_function
        self.start_commands = list(start_commands)
        self.first_time_commands = list(first_time_commands)
        self.supress_output = supress_output

    def initialize(self, start: Start, automaton: Automaton):
        if start.first_time:
            commands = self.first_time_commands
        else:
            commands = self.start_commands

        for command in commands:
            input = command
            while True:
                output = automaton.process_and_rethrow_exit(input)
                if isinstance(output, Listen):
                    break
                if not self.supress_output:
                    input = yield output
        yield Listen()


    def __call__(self):
        context = yield ContextRequest()
        automaton = Automaton(self.inner_function, context)
        while True:
            input = yield
            if isinstance(input, Start):
                yield from self.initialize(input, automaton)
            else:
                output = automaton.process_and_rethrow_exit(input)
                yield output

