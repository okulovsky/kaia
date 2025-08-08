from unittest import TestCase
from pstats import FunctionProfile
from dataclasses import dataclass
from avatar.server.format.dataclass_formatter import DataClassFormatter
from datetime import datetime

@dataclass
class C:
    a: int
    b: datetime
    c: 'C'
    d: FunctionProfile

class OldHintsTestCase(TestCase):
    def test(self):
        self.assertEqual(dict(
            a=int, b=datetime, c=C, d=FunctionProfile
        ),
            DataClassFormatter.get_type_hints(C)
        )

