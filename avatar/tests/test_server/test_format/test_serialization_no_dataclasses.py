import json
from typing import Optional, Union
from unittest import TestCase
from avatar.server.messaging_component.format import Format
from dataclasses import dataclass



@dataclass
class C:
    a: int
    b: str
    c: Optional['C'] = None



class SerializationTestCase(TestCase):
    def check(self, value, _type, alternalive_expected_value = None):
        js = Format.to_json(value, _type)
        new_value = Format.from_json(js, _type)
        if alternalive_expected_value is None:
            self.assertEqual(value, new_value, js)
        else:
            self.assertEqual(alternalive_expected_value, new_value, js)
        self.assertNotIn('@base64' , json.dumps(js))


    def test_none(self):
        self.check(None, None)
        self.check(None, int|None)
        self.check(None, dict|None)
        self.check(None, Optional[int])
        self.check(None, Optional[dict])
        self.check(None, Union[int, None])

        with self.assertRaises(ValueError):
            self.check(None, int)


    def test_int(self):
        self.check(1, None)
        self.check(1, int)

    def test_float(self):
        self.check(1.1, None)
        self.check(1.1, float)

    def test_bool(self):
        self.check(True, None)
        self.check(True, bool)

    def test_str(self):
        self.check('abc', None)
        self.check('abc', str)

    def test_list(self):
        self.check([1,2,3], None)
        self.check([1, 2, 3], list)
        self.check([1, 2, 3], list[int])

    def test_tuple(self):
        self.check((1,2,3), None, [1,2,3])
        self.check((1, 2, 3), tuple)
        self.check((1, 2, 3), tuple[int])


    def test_dict(self):
        d = dict(a=1, b=2)
        self.check(d, None)
        self.check(d, dict)
        self.check(d, dict[str, int])


