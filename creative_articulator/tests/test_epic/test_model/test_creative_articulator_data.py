import shutil
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import mkdtemp

from creative_articulator.common import Node
from creative_articulator.epic.model import (
    Algorithms, BlockType, CreativeArticulatorData, CreativeArticulatorLocations,
    CreativeArticulatorSettings, IdToNode, NodeData, NodeType, Separation, TextCache
)
from creative_articulator.epic.model.model import restore_consistency

from .support import FakeLoader

NAMESPACES = ('creative_articulator.epic.model.basics',)

TEXT = (
    '# Chapter one\n'
    '\n'
    'The house stood at the edge of the forest.\n'
    'Nobody had lived there for many years.\n'
    '\n'
    '- Do you hear that? asked Anna.\n'
    '- I hear nothing at all, said Peter.\n'
    '\n'
    '## Chapter two\n'
    '\n'
    ' they enter the house\n'
    '   they find the letter\n'
    'The door was not locked.\n'
)


class DataTestCase(unittest.TestCase):
    def setUp(self):
        self.folder = Path(mkdtemp())
        self.loader = FakeLoader()
        self.settings = CreativeArticulatorSettings(
            CreativeArticulatorLocations(self.folder),
            NAMESPACES,
            self.loader,
            Algorithms(max_block_length=120)
        )

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def create(self) -> CreativeArticulatorData:
        return CreativeArticulatorData(Node(), self.settings)

    def synchronized(self) -> CreativeArticulatorData:
        data = self.create()
        data.synchronize()
        return data

    def nodes(self, data: CreativeArticulatorData, node_type: int) -> list[Node]:
        return [n for n in data.root.descendants() if n[NodeData].node_type == node_type]

    def ids(self, data: CreativeArticulatorData) -> set[str]:
        return set(n[NodeData].id for n in data.root.descendants())


class TestSynchronize(DataTestCase):
    def setUp(self):
        super().setUp()
        self.loader.set_text('file-1', TEXT)

    def test_tree_is_file_sections_blocks(self):
        data = self.synchronized()
        file = self.nodes(data, NodeType.File)[0]
        self.assertEqual(2, len(file.children))
        for section in file.children:
            self.assertEqual(NodeType.Section, section[NodeData].node_type)
            self.assertGreater(len(section.children), 0)
            for block in section.children:
                self.assertEqual(NodeType.Block, block[NodeData].node_type)

    def test_titles_come_from_the_headers(self):
        data = self.synchronized()
        sections = self.nodes(data, NodeType.Section)
        self.assertEqual(['Chapter one', 'Chapter two'], [s[NodeData].title for s in sections])

    def test_text_is_preserved_by_the_split(self):
        data = self.synchronized()
        file = self.nodes(data, NodeType.File)[0]
        sections = '\n'.join(s[TextCache].text for s in file.children)
        self.assertEqual(TEXT, sections)
        for section in file.children:
            self.assertEqual(section[TextCache].text, '\n'.join(b[TextCache].text for b in section.children))

    def test_separations_follow_the_children(self):
        data = self.synchronized()
        file = self.nodes(data, NodeType.File)[0]
        self.assertEqual([s[NodeData].id for s in file.children], file[Separation].ids)
        for section in file.children:
            self.assertEqual([b[NodeData].id for b in section.children], section[Separation].ids)

    def test_every_node_is_registered_by_id(self):
        data = self.synchronized()
        id_to_node = data.root[IdToNode]
        for node in data.root.descendants():
            self.assertIs(node, id_to_node[node[NodeData].id])

    def test_simhashes_are_computed_everywhere(self):
        data = self.synchronized()
        for node in data.root.descendants():
            self.assertIsNotNone(node[NodeData].simhash)

    def test_block_types_are_assigned(self):
        data = self.synchronized()
        types = set(b[NodeData].block_type for b in self.nodes(data, NodeType.Block))
        self.assertEqual({BlockType.Caption, BlockType.Plan, BlockType.Text}, types)

    def test_second_synchronization_does_not_refetch(self):
        data = self.synchronized()
        calls = len(self.loader.text_calls)
        data.synchronize()
        self.assertEqual(calls, len(self.loader.text_calls))


class TestReload(DataTestCase):
    def setUp(self):
        super().setUp()
        self.loader.set_text('file-1', TEXT)

    def test_tree_is_restored_from_the_caches(self):
        first = self.synchronized()
        second = self.create()
        second.load()
        self.assertEqual(self.ids(first), self.ids(second))

    def test_restored_nodes_keep_their_text(self):
        first = self.synchronized()
        texts = {n[NodeData].id: n[TextCache].text for n in first.root.descendants()}
        second = self.create()
        second.load()
        self.assertEqual(texts, {n[NodeData].id: n[TextCache].text for n in second.root.descendants()})

    def test_loading_does_not_call_the_loader(self):
        self.synchronized()
        calls = len(self.loader.text_calls)
        second = self.create()
        second.load()
        self.assertEqual(calls, len(self.loader.text_calls))


class TestEditing(DataTestCase):
    def setUp(self):
        super().setUp()
        self.loader.set_text('file-1', TEXT)

    def test_small_edit_keeps_the_ids(self):
        data = self.synchronized()
        before = self.ids(data)
        data.update('file-1', TEXT.replace('Peter', 'Pyotr'))
        self.assertEqual(before, self.ids(data))

    def test_small_edit_updates_the_text(self):
        data = self.synchronized()
        data.update('file-1', TEXT.replace('Peter', 'Pyotr'))
        blocks = [b[TextCache].text for b in self.nodes(data, NodeType.Block)]
        self.assertTrue(any('Pyotr' in text for text in blocks))
        self.assertFalse(any('Peter' in text for text in blocks))

    def test_new_section_is_added_and_the_old_ones_survive(self):
        data = self.synchronized()
        before = self.ids(data)
        data.update('file-1', TEXT + '\n## Chapter three\n\nAnd then they left the house.\n')
        self.assertEqual(3, len(self.nodes(data, NodeType.Section)))
        self.assertTrue(before < self.ids(data))

    def test_removed_section_disappears_from_the_tree_and_the_map(self):
        data = self.synchronized()
        removed = self.nodes(data, NodeType.Section)[1]
        removed_ids = set(n[NodeData].id for n in removed.descendants(include_self=True))
        data.update('file-1', TEXT[:TEXT.index('## Chapter two')])
        self.assertEqual(1, len(self.nodes(data, NodeType.Section)))
        self.assertEqual(set(), removed_ids & set(data.root[IdToNode]))

    def test_simhash_of_the_file_follows_the_text(self):
        data = self.synchronized()
        file = self.nodes(data, NodeType.File)[0]
        before = file[NodeData].simhash
        data.update('file-1', TEXT + '\n## Chapter three\n\nAnd then they left the house.\n')
        self.assertNotEqual(before, file[NodeData].simhash)

    def test_updated_tree_survives_a_reload(self):
        data = self.synchronized()
        data.update('file-1', TEXT + '\n## Chapter three\n\nAnd then they left the house.\n')
        expected = self.ids(data)
        second = self.create()
        second.load()
        self.assertEqual(expected, self.ids(second))


class TestFiles(DataTestCase):
    def test_new_file_appears_in_the_structure(self):
        self.loader.set_text('file-1', TEXT)
        data = self.synchronized()
        self.assertEqual(1, len(self.nodes(data, NodeType.File)))
        self.loader.set_text('file-2', '# Another\n\nAnother text entirely.\n')
        data.synchronize()
        self.assertEqual(2, len(self.nodes(data, NodeType.File)))

    def test_deleted_file_disappears(self):
        self.loader.set_text('file-1', TEXT)
        self.loader.set_text('file-2', '# Another\n\nAnother text entirely.\n')
        data = self.synchronized()
        del self.loader.texts['file-2']
        data.synchronize()
        self.assertEqual(['file-1'], [n[NodeData].id for n in self.nodes(data, NodeType.File)])

    def test_file_without_a_single_non_blank_line_still_lands_in_the_tree(self):
        self.loader.set_text('file-1', TEXT)
        self.loader.set_text('file-2', '   \n\n')
        data = self.synchronized()
        self.assertEqual(['file-1', 'file-2'], [n[NodeData].id for n in self.nodes(data, NodeType.File)])

    def test_a_file_line_never_swallows_the_next_one(self):
        self.loader.set_text('file-1', TEXT)
        self.loader.set_text('file-2', 'Another text entirely.\n')
        self.synchronized()
        structure = self.settings.locations.structure
        structure.write_text(structure.read_text().replace(' | file-2', ' | file-2', 1).replace('\nAnother', '\n    Another'), encoding='utf-8')
        data = self.create()
        data.synchronize()
        self.assertEqual(['file-1', 'file-2'], sorted(n[NodeData].id for n in self.nodes(data, NodeType.File)))

    def test_refetch_happens_only_when_the_source_changed(self):
        self.loader.set_text('file-1', TEXT)
        data = self.synchronized()
        self.loader.set_text('file-1', TEXT + '\nOne more line.\n', datetime.now(timezone.utc) + timedelta(minutes=1))
        calls = len(self.loader.text_calls)
        data.synchronize()
        self.assertEqual(calls + 1, len(self.loader.text_calls))


class TestConsistency(DataTestCase):
    def setUp(self):
        super().setUp()
        self.loader.set_text('file-1', TEXT)

    def test_a_healthy_tree_is_left_alone(self):
        data = self.synchronized()
        self.assertEqual([], restore_consistency(data))

    def test_a_block_deleted_by_hand_takes_the_whole_file_down(self):
        data = self.synchronized()
        block = self.nodes(data, NodeType.Block)[0]
        shutil.rmtree(self.settings.locations.block_caches / block[NodeData].id)
        deleted = restore_consistency(data)
        self.assertIn(self.settings.locations.file_caches / 'file-1', deleted)

    def test_damaged_cache_is_recovered_by_the_next_synchronization(self):
        data = self.synchronized()
        block = self.nodes(data, NodeType.Block)[0]
        shutil.rmtree(self.settings.locations.block_caches / block[NodeData].id)
        recovered = self.create()
        recovered.synchronize()
        self.assertEqual(2, len(self.nodes(recovered, NodeType.Section)))
        self.assertEqual([], restore_consistency(recovered))

    def test_orphan_block_folders_are_collected(self):
        data = self.synchronized()
        orphan = self.settings.locations.block_caches / 'orphan'
        shutil.copytree(
            self.settings.locations.block_caches / self.nodes(data, NodeType.Block)[0][NodeData].id,
            orphan
        )
        self.assertIn(orphan, restore_consistency(data))


if __name__ == '__main__':
    unittest.main()
