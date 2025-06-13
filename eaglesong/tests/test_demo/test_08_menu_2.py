from eaglesong.tests.test_demo.common import *
from eaglesong.demo.example_08_menu_2 import bot
from eaglesong.drivers.telegram.menu import MenuItem
from eaglesong.drivers.telegram.primitives import Options, SelectedOption,Delete


class Demo0TestCase(TestCase):
    def test_options(self):
        (
            S(bot)
            .send('/start')
            .check(lambda z: '/menu' in z)
            .send('/menu')
            .check(Options)
            .send(SelectedOption('Small talk'))
            .check(Delete, Options)
            .send(SelectedOption('Naughty'))
            .check(Delete, lambda z: 'horny' in z, Options)
            .send(SelectedOption('Nice'))
            .check(Delete, lambda z: 'handsome' in z)
            .validate()

        )

    def test_buttons(self):
        (
            S(bot)
            .send('/start')
            .check(lambda z: '/menu' in z)
            .send('/menu')
            .check(lambda z: z.options==('Weather', 'Small talk', 'Time', MenuItem.close_button_text))
            .send(SelectedOption('Small talk'))
            .check(Delete, lambda z: z.options==('Nice', 'Naughty', MenuItem.back_button_text, MenuItem.close_button_text))
            .send(SelectedOption(MenuItem.back_button_text))
            .check(Delete, lambda z: z.options==('Weather', 'Small talk', 'Time', MenuItem.close_button_text))
            .send(SelectedOption(MenuItem.close_button_text))
            .check(Delete)
            .validate()
        )

    def test_reload(self):
        s = (
            S(bot)
            .send('/start')
            .send('/menu')
            .send(SelectedOption('Time'))
            .check(Delete, Scenario.stash('time1'))
            .wait(0.1)
            .send(SelectedOption(MenuItem.reload_button_text))
            .check(Delete, Scenario.stash('time2'))
            .validate()
        )
        self.assertNotEqual(s.stashed_values['time1'], s.stashed_values['time2'])





