"""
You can also associate custom actions with menu items.

The first way is to create a class inherited from `MenuItem`, and implement it's `run` method.

Alternatively, you can just write the Routine in the function and create `FunctionalMenuItem` in it.
"""

from eaglesong.demo.common import *
from eaglesong.drivers.telegram import menu
import requests


class WeatherMenu(menu.MenuItem):
    def __init__(self, city, lat, long):
        self.city = city
        self.lat = lat
        self.long = long

    def run(self):
        response = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.long}&current_weather=true')
        temp = response.json()['current_weather']['temperature']
        yield f"Temperature in {self.city}: {temp}"

    def get_caption(self):
        return self.city


def say_nice_thing():
    yield "You are handsome!"

def say_naugty_thing():
    yield "I'm horny!"



def create_menu():
    main = (
        menu.MenuFolder('Select an option').items(
            menu.MenuFolder('Weather').items(
                WeatherMenu("Yekaterinburg",56.83, 60.58),
                WeatherMenu("Berlin",52.52,13.40)
            ),
            menu.MenuFolder('Small talk').items(
                menu.FunctionalMenuItem('Nice', say_nice_thing),
                menu.FunctionalMenuItem('Naughty', say_naugty_thing, terminates_menu=False)
            ),
            menu.MenuFolder(lambda: str(datetime.now()), 'Time', True)
        )
    )
    return main

def main():
    yield f'Hi! Say anything and I will repeat. Or open /menu'
    while True:
        input_text = yield Listen()
        if input_text == '/menu':
            yield from create_menu()()
            continue
        yield input_text


bot = Bot("menu", main)

if __name__ == '__main__':
    run(bot)