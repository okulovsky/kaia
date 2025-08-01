import regex
from unittest import TestCase
from grammatron.dubs.algorithms.regex.regex_builder import *

ITERATION = ('iteration',)
OPTION = ('option',)
BEFORE = ('before',)
AFTER = ('after',)

class IterationBuilderTestCase(TestCase):
    def test_iteration(self):
        inside = SequenceParserInstruction((
            ConstantParserInstruction('1'),
            VariableParserInstruction(OPTION),
            ConstantParserInstruction('9')
        ))
        inside_pd = ParserData(
            inside,
            {OPTION: VariableInfo({'q':'q', 'w':'w'})}
        )
        root = SequenceParserInstruction((
            VariableParserInstruction(BEFORE),
            IterationParserInstruction(
                SubdomainInstruction(
                    ITERATION,
                    inside_pd
                )),
            VariableParserInstruction(AFTER)
        ))
        iteration_pd = ParserData(
            root,
            {
                BEFORE: VariableInfo({'a':'a', 'b':'b'}),
                AFTER: VariableInfo({'x': 'x', 'y': 'y'})
            }
        )

        builder = BuilderForParserInstruction(iteration_pd.root, iteration_pd.variables)
        builder.build()

        self.assertEqual(
            {('before',): 'b', ('iteration',): [{('option',): 'w'}, {('option',): 'q'}], ('after',): 'x'},
            builder.parse('b1w91q9x')
        )






