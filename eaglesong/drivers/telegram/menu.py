from ...core import *
from .primitives import Options, SelectedOption, Delete
from copy import deepcopy
from enum import Enum
from abc import ABC, abstractmethod

class TerminateMenu:
    def __init__(self, value = None):
        self.value = value



class MenuItem:
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

    @abstractmethod
    def __call__(self):
        pass


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

    def __call__(self):
        yield from self.method()
        if self.terminates_menu:
            return TerminateMenu()


class ValueMenuItem(MenuItem):
    def __init__(self, caption: Union[Callable, str], value: Any = None):
        self.caption = caption
        self.value = value

    def get_caption(self) -> str:
        return callable_or_value(self.caption)

    def __call__(self):
        yield
        if self.value is not None:
            value = self.value
        else:
            value = self.get_caption()
        return TerminateMenu(value)


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


    def __call__(self):
        while True:
            options, map = self.build_menu()
            expectations = [SelectedOption(o) for o in options.options]
            message_id = yield options
            input = yield Listen()
            yield Delete(message_id)
            if not isinstance(input, SelectedOption):
                return TerminateMenu()
            if input.value == MenuItem.reload_button_text:
                continue
            if input.value == MenuItem.back_button_text:
                return
            if input.value == MenuItem.close_button_text:
                return TerminateMenu()
            if input.value not in map:
                continue

            item = map[input.value]
            item._is_root = False
            returned = yield from item()
            if isinstance(returned, TerminateMenu):
                return returned
            else:
                continue


class MainMenu(MenuItem):
    def __init__(self, content: MenuFolder):
        self.content = content


    def __call__(self):
        content = deepcopy(self.content)
        returned = yield from content()
        if returned is None:
            return None
        if not isinstance(returned, TerminateMenu):
            raise ValueError(f'Internal error: MainMenu should always receive TerminateMenu, but received {returned}')
        return returned.value

