import unittest

from creative_articulator.epic.model import Paragraph, ParagraphArray, ParagraphType, simhash


class TestClassification(unittest.TestCase):
    def _type(self, line: str) -> ParagraphType:
        return ParagraphArray.parse(line)[0].text_type

    def test_blank(self):
        self.assertEqual(ParagraphType.Blank, self._type(''))
        self.assertEqual(ParagraphType.Blank, self._type('   '))

    def test_separator(self):
        self.assertEqual(ParagraphType.Separator, self._type('***'))
        self.assertEqual(ParagraphType.Separator, self._type('  ***  '))

    def test_header(self):
        self.assertEqual(ParagraphType.Header, self._type('# Chapter'))
        self.assertEqual(ParagraphType.Header, self._type('## Chapter'))
        self.assertEqual(ParagraphType.Header, self._type('#no space'))

    def test_plan_is_an_indented_line(self):
        self.assertEqual(ParagraphType.Plan, self._type(' they meet'))
        self.assertEqual(ParagraphType.Plan, self._type('    they part'))

    def test_dialog(self):
        for prefix in ('-', '–', '—'):
            self.assertEqual(ParagraphType.Dialog, self._type(f'{prefix} Hello, he said'))

    def test_plain(self):
        self.assertEqual(ParagraphType.Plain, self._type('He said nothing at all.'))

    def test_indented_dialog_is_a_plan(self):
        self.assertEqual(ParagraphType.Plan, self._type(' - not a dialog, an indented line'))


class TestParagraph(unittest.TestCase):
    def test_text_adds_the_newline_back(self):
        self.assertEqual('abc\n', Paragraph('abc', ParagraphType.Plain).text)

    def test_indent(self):
        self.assertEqual(0, Paragraph('abc', ParagraphType.Plain).indent)
        self.assertEqual(3, Paragraph('   abc', ParagraphType.Plan).indent)

    def test_header_level_and_title(self):
        header = ParagraphArray.parse('## Chapter two')[0]
        self.assertEqual(2, header.header_level)
        self.assertEqual('Chapter two', header.title)

    def test_header_level_of_a_non_header_is_zero(self):
        self.assertEqual(0, Paragraph('plain', ParagraphType.Plain).header_level)


class TestParagraphArray(unittest.TestCase):
    TEXT = '# Title\n\nSome text.\n\n- A dialog line\n***\n'

    def test_parsing_keeps_every_line(self):
        self.assertEqual(len(self.TEXT.split('\n')), len(ParagraphArray.parse(self.TEXT)))

    def test_text_round_trips(self):
        self.assertEqual(self.TEXT, ParagraphArray.parse(self.TEXT).text)

    def test_empty_text_is_one_blank_paragraph(self):
        array = ParagraphArray.parse('')
        self.assertEqual(1, len(array))
        self.assertEqual(ParagraphType.Blank, array[0].text_type)

    def test_simhash_is_precomputed_and_matches_the_text(self):
        array = ParagraphArray.parse(self.TEXT)
        self.assertEqual(simhash(self.TEXT), array.simhash)

    def test_equal_texts_have_equal_simhashes(self):
        self.assertEqual(ParagraphArray.parse(self.TEXT).simhash, ParagraphArray.parse(self.TEXT).simhash)

    def test_subarray_is_a_paragraph_array_with_its_own_simhash(self):
        array = ParagraphArray.parse(self.TEXT)
        part = array.subarray(0, 3)
        self.assertIsInstance(part, ParagraphArray)
        self.assertEqual(3, len(part))
        self.assertEqual(simhash(part.text), part.simhash)

    def test_join_concatenates(self):
        array = ParagraphArray.parse(self.TEXT)
        joined = ParagraphArray.join([array.subarray(0, 3), array.subarray(3, len(array))])
        self.assertEqual(array.text, joined.text)
        self.assertIsInstance(joined, ParagraphArray)

    def test_is_immutable(self):
        array = ParagraphArray.parse(self.TEXT)
        with self.assertRaises(TypeError):
            array[0] = Paragraph('x', ParagraphType.Plain)

    def test_has_type(self):
        array = ParagraphArray.parse(self.TEXT)
        self.assertTrue(array.has_type(ParagraphType.Dialog))
        self.assertFalse(array.has_type(ParagraphType.Plan))

    def test_length_counts_the_newlines(self):
        array = ParagraphArray.parse('ab\ncd')
        self.assertEqual(6, array.length)


if __name__ == '__main__':
    unittest.main()
