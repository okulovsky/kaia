"""
Speaking of `kaia.eaglesong.amenities`, it also contains a very useful Routines
related to button-based menus. In chatbots, it's often very handy to just tap instead of typing.

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

def main(context: BotContext):
    yield create_menu()
    yield f"You have selected: {context.input}"

bot = Bot("menu1", main)
if __name__ == '__main__':
    run(bot)
