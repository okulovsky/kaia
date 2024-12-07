from unittest import TestCase
from kaia.brainbox.core import DeciderState, DeciderInstanceSpec
from kaia.brainbox.core.planers import SimplePlanner, BrainBoxJobForPlanner
from datetime import datetime


class _Gen:
    def __init__(self):
        self.cnt = 0

    def __call__(self, decider, assigned=False):
        self.cnt += 1
        return BrainBoxJobForPlanner(str(self.cnt), decider, None, received_timestamp=datetime(2020, 1, 1 + self.cnt),
                                     assigned=assigned, ordering_token=None)


T = _Gen()


def S(name, st=False):
    return DeciderState(DeciderInstanceSpec(name, None), st)


def Sp(name):
    return DeciderInstanceSpec(name, None)


class SimplePlannerTestCase(TestCase):
    def test_up_alphabet(self):
        plan = SimplePlanner().plan([T('a'), T('a'), T('b'), T('b')], [S('a'), S('b')])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.cool_down)
        self.assertEqual((Sp('a'),), plan.warm_up)

    def test_up_count(self):
        plan = SimplePlanner().plan([T('a'), T('a'), T('b'), T('b'), T('b')], [S('a'), S('b')])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.cool_down)
        self.assertEqual((Sp('b'),), plan.warm_up)

    def test_up_non_ready(self):
        plan = SimplePlanner().plan([T('b')], [S('a'), S('b')])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.cool_down)
        self.assertEqual((Sp('b'),), plan.warm_up)

    def test_up_non_ready_1(self):
        plan = SimplePlanner().plan([], [S('a'), S('b')])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.cool_down)
        self.assertIsNone(plan.warm_up)

    def test_cooldown(self):
        plan = SimplePlanner().plan([T('a'), T('a')], [S('a'), S('b', True)])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.warm_up)
        self.assertEqual((Sp('b'),), plan.cool_down)

    def test_cooldown_1(self):
        plan = SimplePlanner().plan([T('a'), T('a')], [S('a'), S('b', True)])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.warm_up)
        self.assertEqual((Sp('b'),), plan.cool_down)

    def test_no_cooldown(self):
        plan = SimplePlanner().plan([T('a'), T('a'), T('b', True)], [S('a'), S('b', True)])
        self.assertIsNone(plan.assign_tasks)
        self.assertIsNone(plan.warm_up)
        self.assertIsNone(plan.cool_down)

    def test_no_assignment(self):
        plan = SimplePlanner().plan([T('a', True), T('a', True), T('a')], [S('a', True)])
        self.assertIsNone(plan.warm_up)
        self.assertIsNone(plan.cool_down)
        self.assertIsNone(plan.assign_tasks)

    def test_assignment(self):
        T.cnt = 0
        plan = SimplePlanner().plan([T('a', True), T('a')], [S('a', True)])
        self.assertIsNone(plan.warm_up)
        self.assertIsNone(plan.cool_down)
        self.assertEqual(('2',), plan.assign_tasks)

    def test_correct_assignment(self):
        T.cnt = 0
        plan = SimplePlanner().plan(reversed([T('a', True), T('a'), T('a')]), [S('a', True)])
        self.assertIsNone(plan.warm_up)
        self.assertIsNone(plan.cool_down)
        self.assertEqual(('2',), plan.assign_tasks)









