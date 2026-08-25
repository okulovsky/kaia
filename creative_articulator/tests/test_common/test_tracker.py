import unittest

from creative_articulator.common import ITracker, Node, NodeChange


class Foo:
    pass


class Bar:
    pass


class RecordingTracker(ITracker):
    def __init__(self):
        self.changes: list[NodeChange] = []

    def on_change(self, change: NodeChange) -> None:
        self.changes.append(change)


def _install_tracker(root: Node) -> RecordingTracker:
    tracker = RecordingTracker()
    root[ITracker] = tracker
    tracker.changes.clear()  # drop the self-notification of the installation itself
    return tracker


class TestTracker(unittest.TestCase):
    def test_no_tracker_installed_does_not_raise(self):
        root = Node()
        child = Node()
        root.append(child)
        child[Foo] = Foo()
        root.remove(child)

    def test_setitem_tracks_changed(self):
        root = Node()
        tracker = _install_tracker(root)

        root[Foo] = Foo()

        self.assertEqual(len(tracker.changes), 1)
        change = tracker.changes[0]
        self.assertEqual(change.kind, NodeChange.Kind.CHANGED)
        self.assertIs(change.node, root)
        self.assertIs(change.key, Foo)

    def test_ensure_tracks_changed_only_when_created(self):
        root = Node()
        tracker = _install_tracker(root)

        root.ensure(Foo)
        self.assertEqual(len(tracker.changes), 1)
        self.assertEqual(tracker.changes[0].kind, NodeChange.Kind.CHANGED)

        root.ensure(Foo)
        self.assertEqual(len(tracker.changes), 1)

    def test_attach_tracks_changed(self):
        root = Node()
        tracker = _install_tracker(root)

        root.attach(Foo(), Bar)

        self.assertEqual(len(tracker.changes), 1)
        self.assertEqual(tracker.changes[0].kind, NodeChange.Kind.CHANGED)
        self.assertIs(tracker.changes[0].key, Bar)

    def test_append_tracks_added(self):
        root = Node()
        tracker = _install_tracker(root)

        child = Node()
        root.append(child)

        self.assertEqual(len(tracker.changes), 1)
        self.assertEqual(tracker.changes[0].kind, NodeChange.Kind.ADDED)
        self.assertIs(tracker.changes[0].node, child)

    def test_insert_tracks_added(self):
        root = Node()
        tracker = _install_tracker(root)

        child = Node()
        root.insert(0, child)

        self.assertEqual(len(tracker.changes), 1)
        self.assertEqual(tracker.changes[0].kind, NodeChange.Kind.ADDED)
        self.assertIs(tracker.changes[0].node, child)

    def test_remove_tracks_removed(self):
        root = Node()
        child = Node()
        root.append(child)
        tracker = _install_tracker(root)

        root.remove(child)

        self.assertEqual(len(tracker.changes), 1)
        self.assertEqual(tracker.changes[0].kind, NodeChange.Kind.REMOVED)
        self.assertIs(tracker.changes[0].node, child)

    def test_remove_at_tracks_removed(self):
        root = Node()
        child = Node()
        root.append(child)
        tracker = _install_tracker(root)

        root.remove_at(0)

        self.assertEqual(len(tracker.changes), 1)
        self.assertEqual(tracker.changes[0].kind, NodeChange.Kind.REMOVED)
        self.assertIs(tracker.changes[0].node, child)

    def test_moving_child_between_trees_tracks_removed_then_added(self):
        root_a = Node()
        tracker_a = _install_tracker(root_a)

        root_b = Node()
        tracker_b = _install_tracker(root_b)

        child = Node()
        root_a.append(child)
        tracker_a.changes.clear()

        root_b.append(child)

        self.assertEqual(len(tracker_a.changes), 1)
        self.assertEqual(tracker_a.changes[0].kind, NodeChange.Kind.REMOVED)
        self.assertEqual(len(tracker_b.changes), 1)
        self.assertEqual(tracker_b.changes[0].kind, NodeChange.Kind.ADDED)

    def test_delete_tracks_key_removed(self):
        root = Node()
        root[Foo] = Foo()
        tracker = _install_tracker(root)

        root.delete(Foo)

        self.assertEqual(len(tracker.changes), 1)
        change = tracker.changes[0]
        self.assertEqual(change.kind, NodeChange.Kind.KEY_REMOVED)
        self.assertIs(change.node, root)
        self.assertIs(change.key, Foo)
        self.assertFalse(root.has(Foo))

    def test_mutation_on_descendant_routes_to_root_tracker(self):
        root = Node()
        tracker = _install_tracker(root)

        branch = Node()
        root.append(branch)
        leaf = Node()
        branch.append(leaf)
        tracker.changes.clear()

        leaf[Foo] = Foo()

        self.assertEqual(len(tracker.changes), 1)
        self.assertIs(tracker.changes[0].node, leaf)


if __name__ == '__main__':
    unittest.main()
