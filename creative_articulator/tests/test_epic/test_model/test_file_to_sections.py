import unittest

from creative_articulator.epic.model import NodeType, ParagraphArray
from creative_articulator.epic.model.algorithms import file_to_sections

from .support import joined, texts


def sections(text: str):
    return file_to_sections(ParagraphArray.parse(text))


class TestSplitting(unittest.TestCase):
    def test_text_without_headers_is_one_section(self):
        result = sections('Line one.\nLine two.')
        self.assertEqual(['Line one.\nLine two.'], texts(result))

    def test_header_opens_a_section_and_belongs_to_it(self):
        result = sections('# One\n\ntext\n\n# Two\n\nmore text')
        self.assertEqual(['# One\n\ntext\n', '# Two\n\nmore text'], texts(result))

    def test_second_level_header_opens_a_section_too(self):
        result = sections('# One\n\ntext\n\n## Two\n\nmore text')
        self.assertEqual(2, len(result))

    def test_separator_opens_a_section_and_belongs_to_it(self):
        result = sections('text\n***\nmore text')
        self.assertEqual(['text', '***\nmore text'], texts(result))

    def test_headers_in_a_row_stay_in_one_section(self):
        result = sections('# One\n## Two\n***\ntext')
        self.assertEqual(1, len(result))

    def test_leading_header_does_not_produce_an_empty_section(self):
        result = sections('# One\n\ntext')
        self.assertEqual(1, len(result))

    def test_blank_lines_do_not_make_a_section_meaningful(self):
        result = sections('# One\n\n\n## Two\n\ntext')
        self.assertEqual(1, len(result))

    def test_sections_are_a_lossless_partition(self):
        text = '# One\n\ntext\n***\n\n## Two\n\n- dialog\nmore text\n'
        result = sections(text)
        self.assertEqual(text, joined(result))

    def test_empty_text_is_one_section(self):
        self.assertEqual(1, len(sections('')))


class TestNodeData(unittest.TestCase):
    def test_data_is_fully_constructed(self):
        result = sections('# One\n\ntext\n\n## Two\n\nmore')
        for section in result:
            self.assertEqual(NodeType.Section, section.payload.node_type)
            self.assertTrue(section.payload.id)
            self.assertEqual(section.paragraphs.simhash, section.payload.simhash)

    def test_title_comes_from_the_header(self):
        result = sections('# One\n\ntext\n\n## Two\n\nmore')
        self.assertEqual(['One', 'Two'], [s.payload.title for s in result])

    def test_title_is_none_without_a_header(self):
        result = sections('text\n***\nmore text')
        self.assertEqual([None, None], [s.payload.title for s in result])

    def test_ids_are_unique(self):
        result = sections('# One\n\ntext\n\n## Two\n\nmore\n\n## Three\n\nmore')
        self.assertEqual(3, len(set(s.payload.id for s in result)))

    def test_nothing_is_matched_yet(self):
        for section in sections('# One\n\ntext'):
            self.assertIsNone(section.match)


if __name__ == '__main__':
    unittest.main()
