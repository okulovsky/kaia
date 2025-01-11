from unittest import TestCase
from eaglesong.core.translator import *
from eaglesong.core import Automaton, Listen

class Buffer:
    def __init__(self):
        self.buffer = []
        self.counter = 0

    def __call__(self):
        input = yield
        while True:
            self.buffer.append(input)
            input = yield self.counter
            self.counter+=1


class TranslatorTestCase(TestCase):
    def test_input_function(self):
        b = Buffer()
        aut = Automaton(Translator.translate(b).input_function(lambda z: z.outer_input+'1'), None)
        self.assertEqual(0, aut.process('test'))
        self.assertEqual(1, aut.process('test1'))
        self.assertListEqual(['test1', 'test11'], b.buffer)

    def test_input_generator(self):
        def translate(input: TranslatorInputPackage):
            check = yield 'get_'+input.outer_input
            self.assertEqual('file', check)
            return input.outer_input+'1'

        b = Buffer()
        aut = Automaton(Translator.translate(b).input_generator(translate), None)
        self.assertEqual('get_test', aut.process('test'))
        self.assertEqual(0, aut.process('file'))
        self.assertListEqual(['test1'], b.buffer)

    def test_output_function(self):
        b = Buffer()
        aut = Automaton(Translator.translate(b).output_function(lambda z: str(z.inner_output)*2), None)
        self.assertEqual('00', aut.process('test'))
        self.assertEqual('11', aut.process('test1'))
        self.assertListEqual(['test', 'test1'], b.buffer)

    def test_generato_function(self):
        def translate(output: TranslatorOutputPackage):
            yield f'a{output.inner_output}'
            yield f'b{output.inner_output}'

        b = Buffer()
        aut = Automaton(Translator.translate(b).output_generator(translate), None)
        self.assertEqual('a0', aut.process('test'))
        self.assertEqual('b0', aut.process('test1'))
        self.assertEqual('a1', aut.process('test2'))
        self.assertEqual('b1', aut.process('test3'))
        self.assertListEqual(['test', 'test2'], b.buffer)











