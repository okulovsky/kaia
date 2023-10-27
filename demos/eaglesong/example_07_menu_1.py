"""
There is a small `kaia.eaglesong.amenities` library, which currently contains only one thing: button-driver menu.
It is often very handy to program your skills as menus.

The following menu allows you to pick a value from the lists. The value is then displayed to you.
"""
from demos.eaglesong.common import *
from kaia.eaglesong.amenities.menu import *

def create_menu():
    menu = MainMenu(
        MenuFolder("Choose the question").items(
            MenuFolder("Where do you live?").items(
                ValueMenuItem("Europe"),
                ValueMenuItem("Asia"),
                ValueMenuItem("Other")
            ),
            MenuFolder("How old are you?").items(
                ValueMenuItem("<18"),
                ValueMenuItem("18-30"),
                ValueMenuItem("30-40"),
                ValueMenuItem(">40")
            )
        )
    )
    return menu

def main():
    result = yield from create_menu()()
    yield f"You have selected: {result}"

bot = Bot("menu1", main)

if __name__ == '__main__':
    run(bot)
