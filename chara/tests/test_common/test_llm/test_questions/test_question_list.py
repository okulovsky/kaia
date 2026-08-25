import json
import unittest
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from chara.common.llm import Question, QuestionList


class Mood(Enum):
    HAPPY = 'happy'
    SAD = 'sad'


@dataclass
class Weather:
    warm: bool = field(default=False, metadata=dict(desc="Is it warm?"))
    cold: bool = field(default=False, metadata=dict(desc="Is it cold?"))


def _make_questions() -> QuestionList:
    return QuestionList([
        Question('is_friendly', 'Is the character friendly?', bool),
        Question('mood', 'The current mood', Mood),
        Question('age', 'The age of the character', Optional[int], options=[25, None]),
        Question('nickname', 'A nickname', str, options=['Sam', 'Al']),
        Question('rating', 'A rating', int, is_closed=True),
        Question('excited', 'Is the character excited?', bool, is_closed=False),
    ])


class QuestionListTestCase(unittest.TestCase):

    def setUp(self):
        self.questions = _make_questions()

    # --- get_description: closed types get no `etc`, open types (and overrides) do ---

    def test_get_description(self):
        expected = "\n".join([
            '`is_friendly`: Is the character friendly? (`true`, `false`)',
            '`mood`: The current mood (`"HAPPY"`, `"SAD"`)',
            '`age`: The age of the character (`25`, `null` etc)',
            '`nickname`: A nickname (`"Sam"`, `"Al"` etc)',
            '`rating`: A rating (`1`, `2`, `3`)',
            '`excited`: Is the character excited? (`true`, `false` etc)',
        ])
        self.assertEqual(expected, self.questions.get_description())

    # --- get_example: a single valid JSON object, one value per field ---

    def test_get_example_is_valid_json(self):
        example = json.loads(self.questions.get_example())
        self.assertEqual({
            'is_friendly': True,
            'mood': 'HAPPY',
            'age': 25,
            'nickname': 'Sam',
            'rating': 1,
            'excited': True,
        }, example)

    # --- get_format: a JSON schema, delegating to Serializer per field ---

    def test_get_format(self):
        self.assertEqual({
            'type': 'object',
            'properties': {
                'is_friendly': {'type': 'boolean'},
                'mood': {'enum': ['HAPPY', 'SAD']},
                'age': {'anyOf': [{'type': 'integer'}, {'type': 'null'}]},
                'nickname': {'type': 'string'},
                'rating': {'type': 'integer'},
                'excited': {'type': 'boolean'},
            },
            'required': ['is_friendly', 'mood', 'age', 'nickname', 'rating', 'excited'],
        }, self.questions.get_format())

    # --- parse: without dataclass_type, returns a dict with per-field typed values ---

    def test_parse_returns_dict_with_converted_types(self):
        raw = json.dumps({
            'is_friendly': True,
            'mood': 'HAPPY',
            'age': None,
            'nickname': 'Sam',
            'rating': 2,
            'excited': False,
        })
        parsed = self.questions.parse(raw)
        self.assertEqual({
            'is_friendly': True,
            'mood': Mood.HAPPY,
            'age': None,
            'nickname': 'Sam',
            'rating': 2,
            'excited': False,
        }, parsed)

    def test_parse_extracts_json_from_surrounding_text(self):
        raw = 'Here is the answer:\n```json\n' + json.dumps({
            'is_friendly': False,
            'mood': 'SAD',
            'age': 25,
            'nickname': 'Al',
            'rating': 3,
            'excited': True,
        }) + '\n```'
        parsed = self.questions.parse(raw)
        self.assertEqual(Mood.SAD, parsed['mood'])
        self.assertEqual(25, parsed['age'])


class QuestionListFromDataclassTestCase(unittest.TestCase):

    def setUp(self):
        self.questions = QuestionList.from_dataclass(Weather)

    def test_from_dataclass_builds_questions_from_fields(self):
        self.assertEqual(['warm', 'cold'], [q.field_name for q in self.questions.questions])
        self.assertEqual(['Is it warm?', 'Is it cold?'], [q.question for q in self.questions.questions])

    def test_from_dataclass_stores_dataclass_type(self):
        self.assertIs(Weather, self.questions.dataclass_type)

    # --- parse: with dataclass_type set, returns an instance of that dataclass ---

    def test_parse_returns_dataclass_instance(self):
        raw = json.dumps({'warm': True, 'cold': False})
        parsed = self.questions.parse(raw)
        self.assertEqual(Weather(warm=True, cold=False), parsed)


if __name__ == '__main__':
    unittest.main()
