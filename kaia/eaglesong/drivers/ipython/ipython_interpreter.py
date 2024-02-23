from typing import *
from dataclasses import dataclass, field
from ...core import *

@dataclass
class IPythonMessage:
    id: int
    from_bot: bool
    content: Any


@dataclass
class IPythonChatModel:
    messages: Optional[List[IPythonMessage]] = field(default_factory=lambda:[])
    next_id: int = 0


class IPythonInterpreter(Interpreter):
    def __init__(self, automaton: IAutomaton, model: IPythonChatModel):
        self.model = model
        context = BotContext(1)
        super(IPythonInterpreter, self).__init__(automaton)
        self.handle_type_async(Return, self._process_return)
        self.handle_type_async(Listen, self._process_listen)
        self.handle_type_async(Terminate, self._process_terminate)
        self.handle_type_async(str, self._process_content)
        self.handle_type_async(int, self._process_content)
        self.handle_type_async(float, self._process_content)
        self.handle_type_async(Options, self._process_content)
        self.handle_type_async(Media, self._process_content)
        self.handle_type_async(Delete, self._process_delete)

    def _process_listen(self, response: Listen):
        return Interpreter.interrupt_cycle()

    def _process_return(self, response: Return):
        return Interpreter.reset_automaton()

    def _process_terminate(self, response: Terminate):
        self._process_content( f'Error when handling the chat:\n\n{response.message}')
        return Interpreter.reset_automaton()

    def _process_content(self, response):
        self.model.messages.append(IPythonMessage(self.model.next_id, True, response))
        current_id = self.model.next_id
        self.model.next_id+=1
        self.model.is_typing = False
        return Interpreter.continue_cycle(current_id)

    def _process_is_thinking(self, response):
        self.model.is_typing = True
        return Interpreter.continue_cycle()

    def _process_delete(self, response: Delete):
        self.model.messages = [z for z in self.model.messages if z.id!=response.id]
        return Interpreter.continue_cycle()

    def process(self, item):
        self.model.messages.append(IPythonMessage(self.model.next_id, False, item))
        self.model.next_id+=1
        self._process(item)

