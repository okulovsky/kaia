import unittest

from creative_articulator.epic.ai.writing.case import SelectionCase
from creative_articulator.epic.model import Paragraph, ParagraphType, TextCache

from .support import EXAMPLE, initialize


class TestSelectionSpanningTwoParagraphsInOneBlock(unittest.TestCase):
    def setUp(self):
        self.init = initialize(EXAMPLE)
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )

    def test_selection_text_is_unchanged(self):
        self.assertEqual(self.init.selection, self.case.selection.text)
        self.assertEqual('he third block\n3rd paragraph of t', self.case.selection.text)

    def test_selection_paragraphs_and_blocks(self):
        self.assertEqual(
            [
                Paragraph('2nd paragraph of the third block', ParagraphType.Plain),
                Paragraph('3rd paragraph of the third block', ParagraphType.Plain),
            ],
            list(self.case.selection.paragraphs),
        )
        self.assertEqual([self.init.blocks[4]], self.case.selection.blocks)

    def test_before_and_after_share_the_same_block(self):
        self.assertIs(self.case.before.block, self.case.after.block)
        self.assertIs(self.case.before.block, self.init.blocks[4])

    def test_before_context(self):
        self.assertEqual('2nd paragraph of t', self.case.before.text)
        self.assertEqual(
            [Paragraph('1st paragraph of the third block', ParagraphType.Plain)],
            list(self.case.before.paragraphs),
        )

    def test_after_context(self):
        self.assertEqual('he third block', self.case.after.text)
        self.assertEqual(
            [Paragraph('4th paragraph of the fourth block', ParagraphType.Plain)],
            list(self.case.after.paragraphs),
        )

    def test_reconstructs_the_original_file_text(self):
        reconstructed = self.init.before_selection + self.case.selection.text + self.init.after_selection
        self.assertEqual(self.init.file_node[TextCache].text, reconstructed)


class TestSelectionEntirelyInsideOneParagraph(unittest.TestCase):
    def setUp(self):
        self.init = initialize('''
Just a si^ngle li$ne here.''')
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )

    def test_selection(self):
        self.assertEqual('ngle li', self.case.selection.text)

    def test_before_and_after_share_the_same_single_block(self):
        self.assertEqual(1, len(self.init.blocks))
        self.assertIs(self.case.before.block, self.init.blocks[0])
        self.assertIs(self.case.after.block, self.init.blocks[0])

    def test_before_paragraphs_hold_only_the_leading_blank_line(self):
        self.assertEqual([Paragraph('', ParagraphType.Blank)], list(self.case.before.paragraphs))
        self.assertEqual([], list(self.case.after.paragraphs))

    def test_partial_text_on_either_side(self):
        self.assertEqual('Just a si', self.case.before.text)
        self.assertEqual('ne here.', self.case.after.text)


class TestSelectionSpanningMultipleBlocks(unittest.TestCase):
    def setUp(self):
        self.init = initialize('''
Alpha line.
***
Beta li^ne.
***
Gam$ma line.''')
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )

    def test_five_blocks_were_produced(self):
        # Three lines of text, and a block of its own for each of the two
        # separators between them.
        self.assertEqual(5, len(self.init.blocks))

    def test_before_and_after_land_on_different_blocks(self):
        self.assertIs(self.case.before.block, self.init.blocks[2])
        self.assertIs(self.case.after.block, self.init.blocks[4])

    def test_before_and_after_text(self):
        self.assertEqual('Beta li', self.case.before.text)
        self.assertEqual('ma line.', self.case.after.text)

    def test_no_leftover_paragraphs_since_selection_starts_and_ends_mid_line(self):
        self.assertEqual([], list(self.case.before.paragraphs))
        self.assertEqual([], list(self.case.after.paragraphs))

    def test_selection_spans_every_touched_block_including_the_separator(self):
        self.assertEqual(
            [self.init.blocks[2], self.init.blocks[3], self.init.blocks[4]],
            self.case.selection.blocks,
        )


class TestSelectionCrossingASeparatorIntoTheNextBlock(unittest.TestCase):
    def setUp(self):
        self.init = initialize('''
Alph^a
***
Be$ta''')
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )

    def test_three_blocks_were_produced(self):
        self.assertEqual(3, len(self.init.blocks))

    def test_selection_swallows_the_separator(self):
        self.assertEqual('a\n***\nBe', self.case.selection.text)

    def test_before_and_after_land_on_different_blocks(self):
        self.assertIs(self.case.before.block, self.init.blocks[0])
        self.assertIs(self.case.after.block, self.init.blocks[2])

    def test_before_and_after_text(self):
        self.assertEqual('Alph', self.case.before.text)
        self.assertEqual('ta', self.case.after.text)

    def test_before_paragraphs_hold_only_the_leading_blank_line(self):
        self.assertEqual([Paragraph('', ParagraphType.Blank)], list(self.case.before.paragraphs))
        self.assertEqual([], list(self.case.after.paragraphs))


class TestSelectionExactlyCoversTheSeparatorParagraph(unittest.TestCase):
    def setUp(self):
        self.init = initialize('''
Alpha
^***$
Beta''')
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )

    def test_selection_is_exactly_the_separator(self):
        self.assertEqual('***', self.case.selection.text)

    def test_before_and_after_share_the_separators_own_block(self):
        self.assertIs(self.case.before.block, self.init.blocks[1])
        self.assertIs(self.case.after.block, self.init.blocks[1])

    def test_nothing_is_left_over_on_either_side(self):
        # The separator fills its block exactly, so there is no remaining
        # paragraph of that block to report as context on either side.
        self.assertEqual([], list(self.case.before.paragraphs))
        self.assertEqual([], list(self.case.after.paragraphs))
        self.assertEqual('', self.case.before.text)
        self.assertEqual('', self.case.after.text)


class TestCaretRightBeforeTheFirstRealParagraph(unittest.TestCase):
    def setUp(self):
        self.init = initialize('''
^$First line
Second line''')
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )

    def test_selection_is_empty(self):
        self.assertEqual('', self.case.selection.text)

    def test_before_has_no_text_but_keeps_the_leading_blank_line(self):
        self.assertEqual('', self.case.before.text)
        self.assertEqual([Paragraph('', ParagraphType.Blank)], list(self.case.before.paragraphs))

    def test_after_holds_the_paragraph_the_caret_touches_and_the_rest_of_the_block(self):
        self.assertEqual('First line', self.case.after.text)
        self.assertEqual(
            [Paragraph('Second line', ParagraphType.Plain)],
            list(self.case.after.paragraphs),
        )


class TestCaretAtTheEndOfTheFile(unittest.TestCase):
    def setUp(self):
        self.init = initialize('''
First line
Second line^$''')
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )

    def test_selection_is_empty(self):
        self.assertEqual('', self.case.selection.text)

    def test_before_holds_the_paragraph_the_caret_touches_and_the_rest_of_the_block(self):
        self.assertEqual('Second line', self.case.before.text)
        self.assertEqual(
            [Paragraph('', ParagraphType.Blank), Paragraph('First line', ParagraphType.Plain)],
            list(self.case.before.paragraphs),
        )

    def test_after_has_nothing(self):
        self.assertEqual('', self.case.after.text)
        self.assertEqual([], list(self.case.after.paragraphs))


class TestSelectionCoveringAWholeParagraphExactly(unittest.TestCase):
    def setUp(self):
        self.init = initialize('''
Alpha
^Beta$
Gamma''')
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )

    def test_selection_is_the_whole_middle_paragraph(self):
        self.assertEqual('Beta', self.case.selection.text)

    def test_before_and_after_are_the_full_neighboring_paragraphs(self):
        self.assertEqual('', self.case.before.text)
        self.assertEqual(
            [Paragraph('', ParagraphType.Blank), Paragraph('Alpha', ParagraphType.Plain)],
            list(self.case.before.paragraphs),
        )
        self.assertEqual('', self.case.after.text)
        self.assertEqual([Paragraph('Gamma', ParagraphType.Plain)], list(self.case.after.paragraphs))


class TestMismatchedTextRaises(unittest.TestCase):
    def test_wrong_before_selection_raises(self):
        init = initialize(EXAMPLE)
        self.addCleanup(init.tmp.cleanup)
        with self.assertRaises(ValueError):
            SelectionCase.parse(init.file_node, 'not the right prefix', init.selection, init.after_selection)

    def test_wrong_after_selection_raises(self):
        init = initialize(EXAMPLE)
        self.addCleanup(init.tmp.cleanup)
        with self.assertRaises(ValueError):
            SelectionCase.parse(init.file_node, init.before_selection, init.selection, 'not the right suffix')


if __name__ == '__main__':
    unittest.main()
