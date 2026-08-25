import unittest

from creative_articulator.epic.model import BlockType
from creative_articulator.epic.model.algorithms import collate_sections, join_base

from .support import block_fragment


class TestJoinBase(unittest.TestCase):
    def test_consecutive_text_blocks_are_united(self):
        base = (
            block_fragment('# Caption', BlockType.Caption),
            block_fragment('First half of the text', BlockType.Text),
            block_fragment('Second half of the text', BlockType.Text),
            block_fragment(' a plan', BlockType.Plan),
        )
        joined = join_base(base)
        self.assertEqual(3, len(joined))
        self.assertEqual([1, 2, 1], [len(f.payload) for f in joined])
        self.assertEqual('First half of the text\nSecond half of the text', joined[1].paragraphs.text)

    def test_text_blocks_separated_by_a_caption_are_not_united(self):
        base = (
            block_fragment('First text', BlockType.Text),
            block_fragment('# Caption', BlockType.Caption),
            block_fragment('Second text', BlockType.Text),
        )
        self.assertEqual([1, 1, 1], [len(f.payload) for f in join_base(base)])

    def test_original_fragments_are_kept_as_payload(self):
        base = (block_fragment('Some text', BlockType.Text),)
        self.assertIs(base[0], join_base(base)[0].payload[0])


class TestCollateSections(unittest.TestCase):
    def setUp(self):
        self.base = (
            block_fragment('# Chapter one', BlockType.Caption, 'caption-id'),
            block_fragment('The house stood at the edge of the forest.', BlockType.Text, 'text-1'),
            block_fragment('Nobody had lived there for years.', BlockType.Text, 'text-2'),
            block_fragment(' they enter the house', BlockType.Plan, 'plan-id'),
        )

    def test_big_text_block_matches_the_whole_group(self):
        incoming = (
            block_fragment('# Chapter one', BlockType.Caption),
            block_fragment('The house stood at the edge of the forest.\nNobody had lived there for years.'),
            block_fragment(' they enter the house', BlockType.Plan),
        )
        collate_sections(incoming, self.base)
        matched = incoming[1].match.matched_with.payload
        self.assertEqual(['text-1', 'text-2'], [f.payload.id for f in matched])

    def test_caption_and_plan_match_a_single_old_block(self):
        incoming = (
            block_fragment('# Chapter one', BlockType.Caption),
            block_fragment('The house stood at the edge of the forest.\nNobody had lived there for years.'),
            block_fragment(' they enter the house', BlockType.Plan),
        )
        collate_sections(incoming, self.base)
        self.assertEqual(['caption-id'], [f.payload.id for f in incoming[0].match.matched_with.payload])
        self.assertEqual(['plan-id'], [f.payload.id for f in incoming[2].match.matched_with.payload])

    def test_new_block_is_not_matched(self):
        incoming = (block_fragment('An entirely new paragraph nobody has written before.'),)
        collate_sections(incoming, self.base)
        self.assertIsNone(incoming[0].match)

    def test_empty_base_leaves_everything_unmatched(self):
        incoming = (block_fragment('Some text'),)
        collate_sections(incoming, ())
        self.assertIsNone(incoming[0].match)


if __name__ == '__main__':
    unittest.main()
