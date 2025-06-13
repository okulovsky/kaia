from typing import Any
from foundation_kaia.prompters import Referrer, Prompter
from unittest import TestCase
from dataclasses import dataclass

@dataclass
class MyClass:
    a: int
    b: str
    prompt: Any = None

def test(value):
    return str(value*100)

class PrompterTestCase(TestCase):
    def test_prompter(self):
        o = Referrer[MyClass]()
        prompter = Prompter(f"int {o.ref.a}, str {o.ref.b}")
        self.assertEqual("int 12, str 34", prompter(MyClass(12,"34")))
        self.assertEqual('int {{a}}, str {{b}}', prompter.to_readable_string())

    def test_with_formatter(self):
        o = Referrer[MyClass]()
        prompter = Prompter(f"int {o.ref.a/test}")
        self.assertEqual("int 1200", prompter(MyClass(12,"34")))
        self.assertEqual('int {{a}}', prompter.to_readable_string())

    def test_with_dictionary(self):
        d = dict(int=12, str="34")
        o = Referrer()
        prompter = Prompter(f"int {o.ref.int}, str {o.ref.str}")
        self.assertEqual('int 12, str 34', prompter(d))

    def test_with_prompt_propagation(self):
        o = Referrer[MyClass]()
        prompter = Prompter(f"result: {~o.ref.prompt}")
        obj = MyClass(12, '34', lambda z: f"{z.a}/{z.b}")
        self.assertEqual('result: 12/34', prompter(obj))
        self.assertEqual('result: {{prompt(_)}}', prompter.to_readable_string())
