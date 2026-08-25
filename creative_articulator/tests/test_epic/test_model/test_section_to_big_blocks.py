import unittest

from creative_articulator.epic.model import BlockType, NodeType, ParagraphArray, ParagraphType
from creative_articulator.epic.model.algorithms import section_to_big_blocks

from .support import joined, texts


def blocks(text: str):
    return section_to_big_blocks(ParagraphArray.parse(text))


def types(fragments):
    return [f.payload.block_type for f in fragments]


class TestBlockTypes(unittest.TestCase):
    def test_headers_and_separators_form_a_caption_block(self):
        result = blocks('# One\n***\ntext')
        self.assertEqual([BlockType.Caption, BlockType.Text], types(result))
        self.assertEqual('# One\n***', result[0].paragraphs.text)

    def test_plan_gets_an_exclusive_block(self):
        result = blocks('text\n they meet\nmore text')
        self.assertEqual([BlockType.Text, BlockType.Plan, BlockType.Text], types(result))

    def test_plain_and_dialog_share_a_text_block(self):
        result = blocks('text\n- a dialog\nmore text')
        self.assertEqual([BlockType.Text], types(result))

    def test_caption_block_holds_captions_only(self):
        allowed = (ParagraphType.Header, ParagraphType.Separator, ParagraphType.Blank)
        for block in blocks('# One\n\ntext\n\n## Two\n***\n\nmore\n one plan'):
            if block.payload.block_type == BlockType.Caption:
                for paragraph in block.paragraphs:
                    self.assertIn(paragraph.text_type, allowed)

    def test_plan_block_holds_plan_only(self):
        allowed = (ParagraphType.Plan, ParagraphType.Blank)
        for block in blocks('# One\n\ntext\n one plan\n   detail\n\nmore'):
            if block.payload.block_type == BlockType.Plan:
                for paragraph in block.paragraphs:
                    self.assertIn(paragraph.text_type, allowed)


class TestPlanBlocks(unittest.TestCase):
    def test_top_level_plan_line_always_opens_a_block(self):
        result = blocks(' first\n second')
        self.assertEqual([' first', ' second'], texts(result))

    def test_deeper_plan_lines_stay_with_their_top_level_line(self):
        result = blocks(' first\n   detail\n   more detail')
        self.assertEqual(1, len(result))

    def test_plan_tree(self):
        result = blocks(' first\n   detail\n second\n   detail')
        self.assertEqual([' first\n   detail', ' second\n   detail'], texts(result))


class TestPartition(unittest.TestCase):
    TEXT = '# One\n\ntext\n- dialog\n\n one plan\n   detail\n another plan\n\nmore text\n***\n'

    def test_blocks_are_a_lossless_partition(self):
        self.assertEqual(self.TEXT, joined(blocks(self.TEXT)))

    def test_no_block_is_empty(self):
        for block in blocks(self.TEXT):
            self.assertGreater(len(block.paragraphs), 0)

    def test_data_is_fully_constructed(self):
        result = blocks(self.TEXT)
        for block in result:
            self.assertEqual(NodeType.Block, block.payload.node_type)
            self.assertTrue(block.payload.id)
            self.assertEqual(block.paragraphs.simhash, block.payload.simhash)
            self.assertIsNotNone(block.payload.block_type)
        self.assertEqual(len(result), len(set(b.payload.id for b in result)))

    def test_empty_section_has_no_blocks(self):
        self.assertEqual([], section_to_big_blocks(ParagraphArray()))


if __name__ == '__main__':
    unittest.main()
