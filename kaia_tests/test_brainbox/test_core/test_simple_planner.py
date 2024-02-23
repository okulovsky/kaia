from unittest import TestCase
from kaia.brainbox.core import BrainBoxJob, DeciderState, DeciderInstanceSpec
from kaia.brainbox.core.planers import SimplePlanner
from datetime import datetime

class _Gen:
    def __init__(self):
        self.cnt = 0
    def __call__(self, decider, ready = True, assigned = False):
        self.cnt += 1
        return BrainBoxJob(id = str(self.cnt), decider = decider, ready = ready, assigned = assigned)

T = _Gen()


class _Gen1:
    def __init__(self):
        self.cnt = 0
    def __call__(self, assigned = False, ready = True):
        self.cnt += 1
        return BrainBoxJob(
            id = str(self.cnt),
            decider = 'a',
            ready = ready,
            assigned = assigned,
            received_timestamp = datetime(2020,1,1+self.cnt)
        )

R = _Gen1()

def S(name, st = False):
    return DeciderState(DeciderInstanceSpec(name, None), st)

def Sp(name):
    return DeciderInstanceSpec(name, None)


class SimplePlannerTestCase(TestCase):
    def test_up_alphabet(self):
        plan = SimplePlanner().plan([T('a'), T('a'), T('b'), T('b')], [S('a'), S('b') ])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.cool_down)
        self.assertEqual((Sp('a'),), plan.warm_up)

    def test_up_count(self):
        plan = SimplePlanner().plan([T('a'), T('a'), T('b'), T('b'), T('b')], [S('a'), S('b')])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.cool_down)
        self.assertEqual((Sp('b'),), plan.warm_up)

    def test_up_non_ready(self):
        plan = SimplePlanner().plan([T('a', False), T('a', False), T('b')], [S('a'), S('b')])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.cool_down)
        self.assertEqual((Sp('b'),), plan.warm_up)


    def test_up_non_ready_1(self):
        plan = SimplePlanner().plan([T('a', False), T('b', False)], [S('a'), S('b')])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.cool_down)
        self.assertIsNone(plan.warm_up)
        
    def test_cooldown(self):
        plan = SimplePlanner().plan([T('a'), T('a')], [S('a'), S('b', True)])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.warm_up)
        self.assertEqual((Sp('b'),), plan.cool_down)

    def test_cooldown_1(self):
        plan = SimplePlanner().plan([T('a'), T('a'), T('b', False)], [S('a'), S('b', True)])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.warm_up)
        self.assertEqual((Sp('b'),), plan.cool_down)

    def test_no_cooldown(self):
        plan = SimplePlanner().plan([T('a'), T('a'), T('b', assigned=True)], [S('a'), S('b', True)])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.warm_up)
        self.assertIsNone(plan.cool_down)

    def test_no_assignment(self):
        plan = SimplePlanner().plan([R(True), R(True), R()], [S('a', True)])
        self.assertIsNone(plan.warm_up)
        self.assertIsNone(plan.cool_down)
        self.assertIsNone(plan.assign_tasks)

    def test_assignment(self):
        plan = SimplePlanner().plan([R(True), R()], [S('a', True)])
        self.assertIsNone(plan.warm_up)
        self.assertIsNone(plan.cool_down)
        self.assertEqual(('2',), plan.assign_tasks)

    def correct_assignment(self):
        plan = SimplePlanner().plan(reversed([R(True), R(), R()]), [S('a', True)])
        self.assertIsNone(plan.warm_up)
        self.assertIsNone(plan.cool_down)
        self.assertEqual(('2',), plan.assign_tasks)


        






