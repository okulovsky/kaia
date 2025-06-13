from unittest import TestCase
from brainbox.flow import Referrer, Prompter
from dataclasses import dataclass

@dataclass
class MyClass:
    number: int
    s: str

class OntologyPromptTestCase(TestCase):
    def test_prompt(self):
        o = Referrer[MyClass]()
        prompt = Prompter(f"Number {o.ref.number}, string {o.ref.s}")
        data = MyClass(34,'test')
        self.assertEqual('Number 34, string test', prompt(data))




