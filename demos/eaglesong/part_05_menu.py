from typing import *
from kaia.eaglesong.telegram import TgCommand, TgUpdate
from kaia.eaglesong.arch import  Listen, Subroutine
from kaia.eaglesong.amenities.menu import MenuItemOverRoutine, TextMenuItem, AbstractTelegramMenuItem
from demos.eaglesong.common import *
import requests

class WeatherMenu(AbstractTelegramMenuItem):
    def __init__(self, city, lat, long):
        self.city = city
        self.lat = lat
        self.long = long

    def run(self, c):
        response = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.long}&current_weather=true')
        temp = response.json()['current_weather']['temperature']
        yield TgCommand.mock().send_message(c().chat_id, f"Temperature in {self.city}: {temp}")


    def get_caption(self):
        return self.city


def say_nice_thing(c):
    yield TgCommand.mock().send_message(c().chat_id, "You are very handsome!")


def create_menu():
    main = TextMenuItem("Menu", "Select an option", add_back_button=False, add_reload_button=False)
    weather = TextMenuItem('Weather', 'Click to know the weather.', add_reload_button=False)
    weather.add_child(WeatherMenu("Yekaterinburg",56.83, 60.58))
    weather.add_child(WeatherMenu("Berlin",52.52,13.40))
    main.add_child(weather)
    main.add_child(MenuItemOverRoutine("Say something nice", say_nice_thing))
    return main

def main(c):
    yield TgCommand.mock().send_message(
        c().chat_id,
        text=f'Hi {c().update.message.from_user.name}! Say anything and I will repeat. Or open /menu'
    )

    while True:
        yield Listen()
        input_text = c().update.message.text
        if input_text == '/menu':
            yield create_menu()
            continue
        yield TgCommand.mock().send_message(c().chat_id, input_text)

if __name__ == '__main__':
    run(main)