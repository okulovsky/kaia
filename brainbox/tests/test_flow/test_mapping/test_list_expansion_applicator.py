from unittest import TestCase
from brainbox.flow import ListExpansionApplicator, Referrer
from dataclasses import dataclass

@dataclass
class MyItem:
    field_1: str
    field_2: str|None = None
    index_field: int|None = None

class ListExpansionApplicatorTestCase(TestCase):
    def test_list_expansion(self):
        o = Referrer[MyItem]()
        e = ListExpansionApplicator(o.ref.field_2)
        item = MyItem('x')
        result = e.apply(item, ['1','2','3'])
        self.assertEqual(
            [
                {'field_1': 'x', 'field_2': '1', 'index_field':None},
                {'field_1': 'x', 'field_2': '2', 'index_field':None},
                {'field_1': 'x', 'field_2': '3', 'index_field':None}
            ],
            [r.__dict__ for r in result]
        )

    def test_list_expansion_with_index(self):
        o = Referrer[MyItem]()
        e = ListExpansionApplicator(o.ref.field_2, o.ref.index_field)
        item = MyItem('x')
        result = e.apply(item, ['1','2','3'])
        self.assertEqual(
            [
                {'field_1': 'x', 'field_2': '1', 'index_field':0},
                {'field_1': 'x', 'field_2': '2', 'index_field':1},
                {'field_1': 'x', 'field_2': '3', 'index_field':2}
            ],
            [r.__dict__ for r in result]
        )
