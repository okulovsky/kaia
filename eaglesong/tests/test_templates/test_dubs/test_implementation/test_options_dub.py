from eaglesong.tests.test_templates.test_dubs.common import *

import unittest
from enum import Enum



class FruitEnum(Enum):
    APPLE = "apple"
    CARROT = "carrot"
    BANANA = "banana"


class TestOptionsDubConstructor(unittest.TestCase):

    def test_constructor_with_dict(self):
        options = {
            "apple": "fruit",
            "banana": "fruit",
            "carrot": "vegetable"
        }
        dub = OptionsDub(options)
        expected = {
            "fruit": ["apple", "banana"],
            "vegetable": ["carrot"]
        }
        self.assertEqual(dub.value_to_strs, expected)

    def test_constructor_with_enum(self):
        dub = OptionsDub(FruitEnum)
        self.assertEqual(
            {
                FruitEnum.APPLE: ['apple'],
                FruitEnum.CARROT: ['carrot'],
                FruitEnum.BANANA: ['banana'],
            },
            dub.value_to_strs
        )

    def test_constructor_with_iterable(self):
        options = ["yes", "no", "maybe"]
        dub = OptionsDub(options)
        expected = {
            "yes": ["yes"],
            "no": ["no"],
            "maybe": ["maybe"]
        }
        self.assertEqual(dub.value_to_strs, expected)
