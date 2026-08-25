import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brainbox.deciders import Ollama

from chara.common.llm import (
    BrainBoxLLMEngine, BulletPointDivider, ILLM, ILLMEngine, LLMRequest, LLMRequestBuilder,
    LLMSetup, MockLLMEngine, NoOpBuilder, Question, QuestionList,
)

FOLDER = Path(__file__).parent


@dataclass
class Colors:
    warm: list[str]|None = None
    cold: list[str]|None = None


@dataclass
class Weather:
    warm: bool = field(default=False, metadata=dict(desc="Is it warm?"))
    cold: bool = field(default=False, metadata=dict(desc="Is it cold?"))


@dataclass
class Case:
    name: str = 'Alice'
    result: Any = None
    other: Any = None
    image: Any = None
    questions: QuestionList|None = None
    items: list[str] = field(default_factory=list)


def setup(*replies: str) -> LLMSetup:
    return LLMSetup(MockLLMEngine(*replies), 'test-model')


class BuilderTestCase(unittest.TestCase):
    def test_setup_default_is_a_real_builder(self):
        builder = setup().default()
        self.assertIsInstance(builder, LLMRequestBuilder)
        request = builder.template(FOLDER/'case.jinja').to_request()
        self.assertEqual('Hello, Alice!', request.build_prompt(Case()).strip())

    def test_builder_is_immutable(self):
        builder = setup().default()
        builder.system_prompt('x')
        self.assertEqual(0, len(builder.steps))

    def test_request_default_ignores_the_defaults(self):
        request = setup().default().custom_prompt(lambda case: 'MINE').to_request()
        result = request.default().template(FOLDER/'case.jinja').to_request()
        self.assertIs(request, result)
        self.assertEqual('MINE', result.build_prompt(Case()))

    def test_builder_default_ignores_the_defaults(self):
        builder = setup().default().custom_prompt(lambda case: 'MINE')
        defaulted = builder.default()
        self.assertIsInstance(defaulted, NoOpBuilder)
        self.assertEqual('MINE', defaulted.template(FOLDER/'case.jinja').to_request().build_prompt(Case()))

    def test_edit_adds_to_an_existing_request(self):
        request = setup().default().custom_prompt(lambda case: 'MINE').to_request()
        edited = request.edit().assign('result').to_request()
        self.assertEqual(1, len(request.steps))
        self.assertEqual(2, len(edited.steps))
        self.assertEqual(request.setup, edited.setup)

    def test_edit_after_default(self):
        # This is the pipeline pattern: defaults the caller may pre-empt, then a
        # private parser the caller cannot supply.
        caller_request = setup('answer').default().custom_prompt(lambda case: 'MINE').to_request()
        for source in (setup('answer'), caller_request):
            request = source.default().template(FOLDER/'case.jinja').to_request()
            request = request.edit().parse(lambda case, output: output.upper()).assign('result').to_request()
            case = Case()
            self.assertEqual('ANSWER', request.execute(case))
            self.assertEqual('ANSWER', case.result)


class PromptTestCase(unittest.TestCase):
    def test_no_prompt_raises(self):
        request = setup().default().assign('result').to_request()
        with self.assertRaises(ValueError) as e:
            request.build_prompt(Case())
        self.assertIn('No prompt was produced', str(e.exception))

    def test_template_entities(self):
        request = setup().default().template(FOLDER/'entities.jinja').entities(length=5).to_request()
        self.assertEqual('Alice in 5 words.', request.build_prompt(Case()).strip())

    def test_template_entities_callable(self):
        request = (setup().default()
                   .template(FOLDER/'entities.jinja')
                   .entities(length=lambda case: len(case.name))
                   .to_request())
        self.assertEqual('Alice in 5 words.', request.build_prompt(Case()).strip())

    def test_derived_case_wins_over_the_template_in_both_orders(self):
        derived = lambda case: Case(name=case.name.upper())
        first = setup().default().derived_case(derived).template(FOLDER/'case.jinja').to_request()
        second = setup().default().template(FOLDER/'case.jinja').derived_case(derived).to_request()
        self.assertEqual('Hello, ALICE!', first.build_prompt(Case()).strip())
        self.assertEqual('Hello, ALICE!', second.build_prompt(Case()).strip())

    def test_system_prompt_and_model_reach_the_task(self):
        request = setup().default().custom_prompt(lambda case: 'P').system_prompt('S').to_request()
        task = request.create_task(Case())
        self.assertEqual('Ollama', task.decider)
        self.assertEqual('question', task.method)
        self.assertEqual('test-model', task.optionals.parameter)
        self.assertEqual('P', task.arguments['prompt'])
        self.assertEqual('S', task.arguments['system_prompt'])


class OptionsTestCase(unittest.TestCase):
    def _options(self, builder) -> Ollama.Options:
        return builder.custom_prompt(lambda case: 'P').to_request().create_task(Case()).arguments['options']

    def test_no_options(self):
        self.assertIsNone(self._options(setup().default()))

    def test_last_wins_per_field(self):
        options = self._options(setup().default().options(temperature=0.1, top_k=5).options(temperature=0.9))
        self.assertEqual(0.9, options.temperature)
        self.assertEqual(5, options.top_k)

    def test_none_does_not_clobber(self):
        options = self._options(setup().default().options(temperature=0.1).options(Ollama.Options(temperature=None)))
        self.assertEqual(0.1, options.temperature)

    def test_none_options_object(self):
        options = self._options(setup().default().options(None).options(temperature=0.1))
        self.assertEqual(0.1, options.temperature)


class ResultTypizationTestCase(unittest.TestCase):
    def test_object(self):
        reply = 'Sure!\n```json\n{"warm": ["red"], "cold": ["blue"]}\n```\n'
        request = setup(reply).default().custom_prompt(lambda case: 'P').result_type(Colors).assign('result').to_request()
        case = Case()
        self.assertEqual(Colors(['red'], ['blue']), request.execute(case))
        self.assertEqual(Colors(['red'], ['blue']), case.result)

    def test_array(self):
        request = setup('["a", "b"]').default().custom_prompt(lambda case: 'P').result_type(list[str]).to_request()
        self.assertEqual(['a', 'b'], request.execute(Case()))

    def test_format_is_set(self):
        request = setup().default().custom_prompt(lambda case: 'P').result_type(Colors).to_request()
        options = request.create_task(Case()).arguments['options']
        self.assertIn('$defs', options.format)

    def _entities(self, request) -> dict:
        entities = {}
        for step in request.steps:
            step.fill_template_entities(Case(), entities)
        return entities

    def test_example_entity_comes_from_the_given_example(self):
        request = (setup().default()
                   .result_type(Colors, Colors(['red'], ['blue']))
                   .custom_prompt(lambda case: 'P')
                   .to_request())
        self.assertEqual(
            '{\n  "warm": [\n    "red"\n  ],\n  "cold": [\n    "blue"\n  ]\n}',
            self._entities(request)['example'],
        )

    def test_no_example_no_entity(self):
        request = setup().default().result_type(Colors).custom_prompt(lambda case: 'P').to_request()
        self.assertNotIn('example', self._entities(request))

    def test_questionnaire_and_result_type_refuse_to_share_a_request(self):
        questions = QuestionList([Question('warm', 'Is it warm?', bool)])
        for builder in (
            setup().default().questionnaire(questions).result_type(Colors),
            setup().default().result_type(Colors).questionnaire(questions),
        ):
            with self.assertRaises(ValueError) as e:
                builder.to_request().build_prompt(Case())
            self.assertIn('not meant to be combined', str(e.exception))

    def test_an_explicit_entity_also_collides(self):
        request = (setup().default()
                   .entities(example='mine')
                   .result_type(Colors, Colors(['red']))
                   .custom_prompt(lambda case: 'P')
                   .to_request())
        with self.assertRaises(ValueError):
            request.build_prompt(Case())


class QuestionnaireTestCase(unittest.TestCase):
    QUESTIONS = QuestionList([Question('warm', 'Is it warm?', bool), Question('cold', 'Is it cold?', bool)])

    def test_from_a_list(self):
        request = setup('{"warm": true, "cold": false}').default().questionnaire(self.QUESTIONS).to_request()
        self.assertEqual(dict(warm=True, cold=False), request.execute(Case()))

    def test_from_a_dataclass(self):
        request = setup('{"warm": true, "cold": false}').default().questionnaire(Weather).to_request()
        self.assertEqual(Weather(True, False), request.execute(Case()))

    def test_from_the_case(self):
        request = setup('{"warm": true, "cold": false}').default().questionnaire('questions').to_request()
        self.assertEqual(dict(warm=True, cold=False), request.execute(Case(questions=self.QUESTIONS)))

    def test_not_a_dataclass(self):
        with self.assertRaises(ValueError):
            setup().default().questionnaire(int)

    def test_the_whole_prompt_is_generated(self):
        request = setup().default().questionnaire(self.QUESTIONS).to_request()
        prompt = request.build_prompt(Case())
        self.assertIn('`warm`: Is it warm?', prompt)
        self.assertIn('Answer these questions in JSON format', prompt)
        self.assertIn('Do not provide any comments or explanations.', prompt)

    def test_the_intro_argument_leads_the_generated_questions(self):
        request = setup().default().questionnaire(self.QUESTIONS, 'Look at this.').to_request()
        prompt = request.build_prompt(Case())
        self.assertTrue(prompt.startswith('Look at this.'))
        self.assertIn('`warm`: Is it warm?', prompt)

    def test_a_callable_intro_reads_the_case(self):
        request = setup().default().questionnaire(self.QUESTIONS, lambda case: f'About {case.name}.').to_request()
        self.assertTrue(request.build_prompt(Case()).startswith('About Alice.'))

    def test_an_earlier_template_becomes_the_intro(self):
        request = setup().default().template(FOLDER/'case.jinja').questionnaire(self.QUESTIONS).to_request()
        prompt = request.build_prompt(Case())
        self.assertTrue(prompt.startswith('Hello, Alice!'))
        self.assertIn('`warm`: Is it warm?', prompt)

    def test_a_template_and_an_intro_together_raise(self):
        request = (setup().default()
                   .template(FOLDER/'case.jinja')
                   .questionnaire(self.QUESTIONS, 'Look at this.')
                   .to_request())
        with self.assertRaises(ValueError) as e:
            request.build_prompt(Case())
        self.assertIn('not from both', str(e.exception))

    def test_format_is_set(self):
        request = setup().default().questionnaire(self.QUESTIONS).to_request()
        options = request.create_task(Case()).arguments['options']
        self.assertEqual(['warm', 'cold'], options.format['required'])


class ImageTestCase(unittest.TestCase):
    def test_path_is_passed_through(self):
        request = setup().default().custom_prompt(lambda case: 'P').image('image').to_request()
        path = FOLDER/'case.jinja'
        self.assertEqual(path, request.create_task(Case(image=path)).arguments['image'])

    def test_non_path_raises(self):
        request = setup().default().custom_prompt(lambda case: 'P').image('image').to_request()
        with self.assertRaises(ValueError) as e:
            request.create_task(Case(image='/tmp/whatever.png'))
        self.assertIn('must be a Path', str(e.exception))


class ApplicationTestCase(unittest.TestCase):
    def test_output_is_returned_unparsed_by_default(self):
        request = setup('raw').default().custom_prompt(lambda case: 'P').to_request()
        self.assertEqual('raw', request.execute(Case()))

    def test_parser_sees_the_case_and_may_return_none(self):
        def merge(case, output):
            case.items.extend(BulletPointDivider()(output))
            return None

        request = setup('* a\n* b').default().custom_prompt(lambda case: 'P').parse(merge).to_request()
        case = Case()
        self.assertIsNone(request.execute(case))
        self.assertEqual(['a', 'b'], case.items)

    def test_several_assignments_are_allowed(self):
        request = (setup('x').default().custom_prompt(lambda case: 'P')
                   .assign('result').assign('other').to_request())
        case = Case()
        request.execute(case)
        self.assertEqual('x', case.result)
        self.assertEqual('x', case.other)

    def test_ambiguous_parser_raises(self):
        request = (setup('x').default().custom_prompt(lambda case: 'P')
                   .parse(lambda case, output: output).result_type(Colors).to_request())
        with self.assertRaises(ValueError) as e:
            request.postprocess_output(Case(), 'x')
        self.assertIn('Parser is ambiguous', str(e.exception))

    def test_divider_outside_a_pipeline_raises(self):
        request = (setup('* a').default().custom_prompt(lambda case: 'P')
                   .parse(divider=BulletPointDivider()).to_request())
        with self.assertRaises(ValueError) as e:
            request.execute(Case())
        self.assertIn('divider must be None', str(e.exception))


class EngineTestCase(unittest.TestCase):
    def test_brainbox_pipeline_refuses_a_foreign_engine(self):
        request = setup().default().custom_prompt(lambda case: 'P').to_request()
        with self.assertRaises(ValueError) as e:
            request.create_brainbox_pipeline()
        self.assertIn('MockLLMEngine', str(e.exception))

    def test_brainbox_pipeline_is_created(self):
        request = LLMSetup(BrainBoxLLMEngine(), 'm').default().custom_prompt(lambda case: 'P').to_request()
        self.assertIsNotNone(request.create_brainbox_pipeline())

    def test_debug_clones_the_engine(self):
        engine = MockLLMEngine('a')
        original = LLMSetup(engine, 'm')
        debugged = original.debug()
        self.assertFalse(original.engine.debug)
        self.assertTrue(debugged.engine.debug)
        self.assertIsNot(original.engine, debugged.engine)

    def test_with_model(self):
        engine = MockLLMEngine('a')
        self.assertEqual(LLMSetup(engine, 'm'), engine.with_model('m'))

    def test_setup_is_reachable_from_every_illm(self):
        llm_setup = setup()
        builder = llm_setup.default().custom_prompt(lambda case: 'P')
        request = builder.to_request()
        for source in (llm_setup, builder, request, request.default()):
            self.assertIsInstance(source, ILLM)
            self.assertIs(llm_setup, source.setup)

    def test_mock_engine_records_the_tasks(self):
        engine = MockLLMEngine('one', 'two')
        request = LLMSetup(engine, 'm').default().custom_prompt(lambda case: 'P-'+case.name).to_request()
        self.assertEqual('one', request.execute(Case('A')))
        self.assertEqual('two', request.execute(Case('B')))
        self.assertEqual(['P-A', 'P-B'], [task.prompt for task in engine.tasks])


class CaseTypizationTestCase(unittest.TestCase):
    def test_wrong_case_raises(self):
        request = setup().default().case_type(Colors).custom_prompt(lambda case: 'P').to_request()
        with self.assertRaises(ValueError):
            request.build_prompt(Case())


if __name__ == '__main__':
    unittest.main()
