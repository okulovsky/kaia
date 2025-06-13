from foundation_kaia.prompters import JinjaPrompter
from unittest import TestCase
from dataclasses import dataclass
from typing import *

@dataclass
class MyClass:
    a: int
    b: str
    prompt: Any = None

class JinjaPrompterTestCase(TestCase):
    def test_jinja(self):
        prompter = JinjaPrompter("int {{a}}, str {{b}}")
        self.assertEqual(
            "int 12, str 34",
            prompter(MyClass(12, "34"))
        )

    def test_jinja_on_dict(self):
        prompter = JinjaPrompter("int {{a}}, str {{b}}")
        self.assertEqual(
            "int 12, str 34",
            prompter(dict(a=12, b="34"))
        )

    def test_jinja_condition(self):
        prompter = JinjaPrompter("{% if a>10 %} {{b}} {% endif %}")
        self.assertEqual(
            "",
            prompter(dict(a=6,b='test'))
        )
        self.assertEqual(
            "test",
            prompter(dict(a=16, b='test')).strip()
        )
