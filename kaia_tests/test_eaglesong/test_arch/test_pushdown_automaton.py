from kaia.eaglesong.arch import *
from unittest import TestCase

def linear_method(c):
    yield 'A'
    yield c() * 2

def simple_subroutine(c):
    yield 'S1'
    yield 'S2'

def calling_method(c):
    yield 'B'
    yield FunctionalSubroutine(simple_subroutine)
    yield 'C'

def param_subroutine(c, param):
    yield param

def calling_param_method(c):
    yield 'D'
    yield FunctionalSubroutine(lambda x : param_subroutine(x, 'Test'))

def branching_method(c):
    if c()==0:
        yield FunctionalSubroutine(lambda x : param_subroutine(x, 'First'))
    else:
        yield FunctionalSubroutine(lambda x : param_subroutine(x, 'Second'))

def subroutine_with_parameter(c, param1='default'):
    yield param1

def param_subroutine_call_default(c):
    yield FunctionalSubroutine(subroutine_with_parameter)

def param_subroutine_call_args(c):
    yield FunctionalSubroutine(subroutine_with_parameter, 'args')

def param_subroutine_call_kwargs(c):
    yield FunctionalSubroutine(subroutine_with_parameter, param1 ='kwargs')


class TestPushdownAutomaton(TestCase):
    def setUp(self):
        self.aut = PushdownAutomaton(FunctionalSubroutine(linear_method))
        self.aut2 = PushdownAutomaton(FunctionalSubroutine(calling_method))
        self.aut3 = PushdownAutomaton(FunctionalSubroutine(calling_param_method))
        self.aut4 = PushdownAutomaton(FunctionalSubroutine(branching_method))

    def raut(self,aut, count, expect):
        for i in range(count-1):
            aut.process('')
        self.assertEqual(expect,aut.process(''))

    def test_simple_reply(self):
        self.raut(self.aut, 1,'A')

    def test_simple_mind_input(self):
        self.aut.process('')
        self.assertEqual(4,self.aut.process(2))

    def test_simple_terminate(self):
        self.aut.process('')
        self.aut.process(1)
        self.assertTrue(isinstance(self.aut.process(''),Return))

    def test_subroutine_entry(self):
        self.raut(self.aut2, 2,'S1')

    def test_subroutine_exit(self):
        self.raut(self.aut2, 4, 'C')

    def test_param_subroutine(self):
        self.raut(self.aut3,2,'Test')

    def test_branching_1(self):
        self.assertEqual('First',self.aut4.process(0))


    def test_branching_2(self):
        self.assertEqual('Second',self.aut4.process(1))

    def test_call_back(self):
        story = []
        writer = lambda nt : story.append((nt.kind,nt.name))
        aut = PushdownAutomaton(FunctionalSubroutine(calling_method), writer)
        self.assertEqual(0, len(story))

        aut.process('')
        self.assertListEqual([('into','calling_method')], story)
        story = []

        aut.process('')
        self.assertListEqual([('into','simple_subroutine')], story)
        story = []

        aut.process('')
        aut.process('')
        self.assertListEqual([('from','simple_subroutine'),('return','calling_method')],story)
        story = []

        aut.process('')
        self.assertListEqual([('from','calling_method')],story)

    def test_param_sub_default(self):
        aut = PushdownAutomaton(FunctionalSubroutine(param_subroutine_call_default))
        self.assertEqual('default',aut.process(''))

    def test_param_sub_args(self):
        aut = PushdownAutomaton(FunctionalSubroutine(param_subroutine_call_args))
        self.assertEqual('args', aut.process(''))

    def test_param_sub_kwargs(self):
        aut = PushdownAutomaton(FunctionalSubroutine(param_subroutine_call_kwargs))
        self.assertEqual('kwargs', aut.process(''))