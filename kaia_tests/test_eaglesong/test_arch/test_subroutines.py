from unittest import TestCase
from kaia.eaglesong.core import *

def Sc(routine):
    return Scenario(lambda: BotContext(123), Routine.ensure(routine), printing=Scenario.default_printing)

class TestAutomaton(TestCase):
    def test_testing(self):
        def method(c):
            yield c.input + 1
        Sc(method).send(3).check(4, Return).validate()
        Sc(method).send(3).check(int, Return).validate(method)
        Sc(method).send(3).check(lambda z: z==4, Return).validate(method)
        self.assertRaises(ValueError, lambda : Sc(method).send(3).check(4).validate())
        self.assertRaises(ValueError, lambda : Sc(method).send(3).check(3, Return).validate())
        self.assertRaises(ValueError, lambda : Sc(method).send(3).check(str, Return).validate())
        self.assertRaises(ValueError, lambda : Sc(method).send(3).check(lambda z: z==5, Return).validate())


    def test_simple_subroutine(self):
        def method(c):
            inp = c.input
            yield 'A'
            yield inp * 2

        Sc(method).send(3).check('A',6, Return).validate()


    def test_class_subroutine(self):
        class A(Routine):
            def __init__(self, v):
                self.v=v
            def run(self, c):
                inp = c.input
                yield 'B'
                yield inp * self.v

        Sc(A(4)).send(3).check('B', 12, Return).preview()


    def test_calling(self):
        def small(c):
            yield "B"
        def caller(c):
            yield 'A'
            yield Subroutine(small)
            yield 'C'
        Sc(caller).send('').check('A','B','C',Return).validate()


    def test_returned_value(self):
        def small(c):
            yield Return(c.input + 1)
        def caller(c):
            s = Subroutine(small)
            yield s
            v1 = c.input
            v2 = s.returned_value()
            yield f"{v1}{v2}"
        Sc(caller).send(3).check('44',Return).validate()

    def test_automaton_over_wrong_function(self):
        def wrong(c):
            pass

        self.assertRaises(ValueError, Automaton(RoutineBase.ensure(wrong), '').reset)

    def test_recursion(self):
        def rec(c, i):
            if i>0:
                yield Subroutine(rec, i-1)
            yield i


        Sc(Subroutine(rec, 10)).send(1).check(*list(range(11))+[Return]).validate()





