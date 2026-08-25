import unittest

from creative_articulator.epic.model import Algorithms, BlockType, NodeType, ParagraphArray, TextFragment

from .support import cached_node, ids, joined, node_with_children, texts

TEXT = (
    '# Chapter one\n'
    'The house stood at the edge of the forest.\n'
    'Nobody had lived there for many years.\n'
    '- Do you hear that? asked Anna.\n'
    '- I hear nothing at all, said Peter.\n'
    '## Chapter two\n'
    ' they enter the house\n'
    '   they find the letter\n'
    'The door was not locked.\n'
)


def empty_node(node_type: int = NodeType.Section):
    return node_with_children([], node_type)


def file_node(algorithms: Algorithms, text: str):
    fragments = algorithms.final_file_to_sections(ParagraphArray.parse(text), empty_node(NodeType.File))
    children = [
        cached_node(NodeType.Section, f'section-{index}', fragment.paragraphs.text, fragment.payload.title)
        for index, fragment in enumerate(fragments)
    ]
    return node_with_children(children, NodeType.File)


def section_node(algorithms: Algorithms, text: str):
    fragments = algorithms.final_section_to_blocks(ParagraphArray.parse(text), empty_node())
    children = [
        cached_node(NodeType.Block, f'block-{index}', fragment.paragraphs.text, None, fragment.payload.block_type)
        for index, fragment in enumerate(fragments)
    ]
    return node_with_children(children)


class TestFinalFileToSections(unittest.TestCase):
    def setUp(self):
        self.algorithms = Algorithms(max_block_length=120)

    def sections(self, text: str, base):
        return self.algorithms.final_file_to_sections(ParagraphArray.parse(text), base)

    def test_without_a_base_everything_is_new(self):
        result = self.sections(TEXT, empty_node(NodeType.File))
        self.assertEqual(2, len(result))
        for fragment in result:
            self.assertIsNone(fragment.match)
            self.assertNotIn('section', fragment.payload.id)

    def test_unchanged_text_reuses_every_id(self):
        base = file_node(self.algorithms, TEXT)
        self.assertEqual(['section-0', 'section-1'], ids(self.sections(TEXT, base)))

    def test_edited_section_keeps_its_id(self):
        base = file_node(self.algorithms, TEXT)
        result = self.sections(TEXT.replace('Peter', 'Pyotr'), base)
        self.assertEqual(['section-0', 'section-1'], ids(result))

    def test_new_section_gets_a_new_id(self):
        base = file_node(self.algorithms, TEXT)
        result = self.sections(TEXT + '## Chapter three\nAnd then they left the house.\n', base)
        self.assertEqual(3, len(result))
        self.assertEqual(['section-0', 'section-1'], ids(result)[:2])
        self.assertNotIn(ids(result)[2], ('section-0', 'section-1'))

    def test_deleted_section_is_simply_not_returned(self):
        base = file_node(self.algorithms, TEXT)
        result = self.sections(TEXT[:TEXT.index('## Chapter two')], base)
        self.assertEqual(['section-0'], ids(result))

    def test_reordered_sections_keep_their_ids(self):
        base = file_node(self.algorithms, TEXT)
        first, second = TEXT.split('## Chapter two')
        result = self.sections('## Chapter two' + second + first, base)
        self.assertEqual(['section-1', 'section-0'], ids(result))

    def test_sections_are_a_lossless_partition(self):
        base = file_node(self.algorithms, TEXT)
        self.assertEqual(TEXT, joined(self.sections(TEXT, base)))


class TestFinalSectionToBlocks(unittest.TestCase):
    def setUp(self):
        self.algorithms = Algorithms(max_block_length=120)

    def blocks(self, text: str, base):
        return self.algorithms.final_section_to_blocks(ParagraphArray.parse(text), base)

    def test_without_a_base_everything_is_new(self):
        result = self.blocks(TEXT, empty_node())
        for fragment in result:
            self.assertNotIn('block', fragment.payload.id)
            self.assertEqual(NodeType.Block, fragment.payload.node_type)
            self.assertIsNotNone(fragment.payload.block_type)

    def test_ids_are_unique(self):
        result = self.blocks(TEXT, empty_node())
        self.assertEqual(len(result), len(set(ids(result))))

    def test_text_is_cut_into_small_blocks(self):
        result = self.blocks(TEXT, empty_node())
        for fragment in result:
            self.assertLessEqual(fragment.paragraphs.length, 120)

    def test_blocks_are_a_lossless_partition(self):
        base = section_node(self.algorithms, TEXT)
        self.assertEqual(TEXT, joined(self.blocks(TEXT, base)))

    def test_unchanged_text_reuses_every_id(self):
        base = section_node(self.algorithms, TEXT)
        result = self.blocks(TEXT, base)
        self.assertEqual([child.fields.node_data.id for child in base.children], ids(result))

    def test_caption_keeps_its_id_when_edited(self):
        base = section_node(self.algorithms, TEXT)
        result = self.blocks(TEXT.replace('# Chapter one', '# Chapter One'), base)
        captions = [f for f in result if f.payload.block_type == BlockType.Caption]
        self.assertEqual('block-0', captions[0].payload.id)

    def test_untouched_blocks_keep_their_ids_after_an_edit(self):
        base = section_node(self.algorithms, TEXT)
        old_ids = [child.fields.node_data.id for child in base.children]
        result = self.blocks(TEXT.replace('Peter', 'Pyotr'), base)
        self.assertGreaterEqual(len(set(old_ids) & set(ids(result))), len(old_ids) - 1)

    def test_new_text_gets_new_ids(self):
        base = section_node(self.algorithms, TEXT)
        old_ids = set(child.fields.node_data.id for child in base.children)
        edited = TEXT + 'An entirely new paragraph nobody has ever written before.\n'
        result = self.blocks(edited, base)
        self.assertTrue(set(ids(result)) - old_ids)

    def test_plan_block_keeps_its_id(self):
        base = section_node(self.algorithms, TEXT)
        plan_ids = [child.fields.node_data.id for child in base.children if child.fields.node_data.block_type == BlockType.Plan]
        result = self.blocks(TEXT, base)
        result_plan_ids = [f.payload.id for f in result if f.payload.block_type == BlockType.Plan]
        self.assertEqual(plan_ids, result_plan_ids)


class TestProxies(unittest.TestCase):
    def test_algorithms_pass_their_settings_to_the_functions(self):
        algorithms = Algorithms(max_block_length=60)
        blocks = algorithms.separate(ParagraphArray.parse(TEXT))
        for block in blocks:
            self.assertTrue(block.paragraphs.length <= 60 or len(block.paragraphs) == 1)

    def test_separation_can_be_overridden_in_a_descendant(self):
        class OneBlockPerParagraph(Algorithms):
            def separate(self, text):
                return [TextFragment(text.subarray(index, index + 1), None) for index in range(len(text))]

        algorithms = OneBlockPerParagraph()
        section = '\n'.join(f'Line number {i}.' for i in range(5))
        result = algorithms.final_section_to_blocks(ParagraphArray.parse(section), empty_node())
        self.assertEqual(5, len(result))
        self.assertEqual(texts(result), section.split('\n'))


if __name__ == '__main__':
    unittest.main()
