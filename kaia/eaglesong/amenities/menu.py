from ..core import *
from copy import deepcopy
from enum import Enum


class TerminateMenu:
    def __init__(self, value = None):
        self.value = value



class MenuItem(Routine):
    def get_caption(self) -> str:
        raise NotImplementedError()

    def get_status(self) -> 'MenuItem.Status':
        return MenuItem.Status.Active

    def is_root(self):
        if not hasattr(self,'_is_root'):
            return True
        return False

    reload_button_text = '⟳'
    back_button_text = '←'
    close_button_text = '✖'

    class Status(Enum):
        Active = 0
        Hidden = 1


def callable_or_value(x):
    if callable(x):
        return x()
    return x

class FunctionalMenuItem(MenuItem):
    def __init__(self,
                 caption: Union[Callable, str],
                 method,
                 terminates_menu = True,
                 ):
        self.caption = caption
        self.method = method
        self.terminates_menu = terminates_menu

    def get_caption(self):
        return callable_or_value(self.caption)

    def run(self, context):
        yield Subroutine.ensure(self.method)
        if self.terminates_menu:
            yield Return(TerminateMenu())


class ValueMenuItem(MenuItem):
    def __init__(self, caption: Union[Callable, str], value: Any = None):
        self.caption = caption
        self.value = value

    def get_caption(self) -> str:
        return callable_or_value(self.caption)

    def run(self, context):
        if self.value is not None:
            value = self.value
        else:
            value = self.get_caption()
        yield Return(TerminateMenu(value))


class MenuFolder(MenuItem):
    def __init__(self,
                 content: Union[Callable[[], str], str],
                 caption: Union[Callable[[], str], str, None] = None,
                 add_reload_button: bool = False
                 ):
        self.content = content
        self.caption = caption
        if self.caption is None:
            self.caption = self.content
        self.add_reload_button = add_reload_button
        self._items = [] #type: List[MenuItem]


    def items(self, *items: MenuItem) -> 'MenuFolder':
        self._items = list(items)
        return self

    def get_caption(self) -> str:
        return callable_or_value(self.caption)

    def build_menu(self) -> Tuple[Options, Dict]:
        content = callable_or_value(self.content)
        buttons = []
        map = {}
        for item in self._items:
            status = item.get_status()
            if status == MenuItem.Status.Hidden:
                continue
            caption = item.get_caption()
            buttons.append(caption)
            map[caption] = item
        if self.add_reload_button:
            buttons.append(MenuItem.reload_button_text)
        if not self.is_root():
            buttons.append(MenuItem.back_button_text)
        buttons.append(MenuItem.close_button_text)
        return Options(content, tuple(buttons)), map


    def run(self, context: BotContext):
        while True:
            options, map = self.build_menu()
            expectations = [SelectedOption(o) for o in options.options]
            yield options
            message_id = context.input
            yield Listen.for_one_of(*expectations)
            input = context.input
            yield Delete(message_id)
            if not isinstance(input, SelectedOption):
                yield Return(TerminateMenu())
            if input.value == MenuItem.reload_button_text:
                continue
            if input.value == MenuItem.back_button_text:
                yield Return()
            if input.value == MenuItem.close_button_text:
                yield Return(TerminateMenu())
            if input.value not in map:
                continue

            item = map[input.value]
            item._is_root = False
            yield item
            returned = item.returned_value()
            if isinstance(returned, TerminateMenu):
                yield Return(returned)
            else:
                continue


class MainMenu(MenuItem):
    def __init__(self, content: MenuFolder):
        self.content = content


    def run(self, context):
        content = deepcopy(self.content)
        yield content
        returned = content.returned_value()
        if returned is None:
            return None
        if not isinstance(returned, TerminateMenu):
            raise ValueError('Internal error: MainMenu should always receive TerminateMenu')
        yield Return(returned.value)

