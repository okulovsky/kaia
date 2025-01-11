from brainbox.framework.common.marshalling.format import Format
from unittest import TestCase
import json

def make(obj):
    s = json.dumps(Format.encode(obj))
    return Format.decode(json.loads(s)), s


class TupleTestCase(TestCase):
    def test_tuples(self):
        rs, _ = make(dict(result=(1,2,3)))
        self.assertIsInstance(rs['result'], tuple)

