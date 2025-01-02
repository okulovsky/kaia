from unittest import TestCase
from eaglesong.core.automaton import Automaton, ContextRequest, Return, Terminate

class AutomatonTestCase(TestCase):
    def test_yield_none(self):
        def f():
            message = yield None
            yield message
            yield 'ok'

        aut = Automaton(f, None)
        self.assertEqual('text', aut.process('text'))
        self.assertEqual('ok', aut.process('text'))

    def test_yield_context_request(self):
        def f():
            context = yield ContextRequest()
            yield context
            yield 'ok'

        aut = Automaton(f, 'context')
        self.assertEqual('context', aut.process('text'))
        self.assertEqual('ok', aut.process('text'))

    def test_raise_return(self):
        def f():
            yield 'ok'
            raise Return()
            yield 'test'

        aut = Automaton(f, None)
        self.assertEqual('ok', aut.process('text'))
        self.assertIsInstance(aut.process('text'), Return)
        self.assertEqual('ok', aut.process('text')) #because Automaton has restarted

    def test_raise_terminate(self):
        def f():
            yield 'ok'
            raise Terminate('error')
            yield 'test'

        aut = Automaton(f, None)
        self.assertEqual('ok', aut.process('text'))
        self.assertIsInstance(aut.process('text'), Terminate)
        self.assertEqual('ok', aut.process('text'))  # because Automaton has restarted

    def test_other_exception(self):
        def f():
            yield 'ok'
            raise ValueError()
        aut = Automaton(f, None)
        self.assertEqual('ok', aut.process('text'))
        self.assertRaises(ValueError, lambda: aut.process('text'))
