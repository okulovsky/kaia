import unittest
from pathlib import Path
from foundation_kaia.releasing.mddoc import parse
from foundation_kaia.releasing.mddoc.doc_block import TextBlock, ExpectedValueBlock
from foundation_kaia.releasing.mddoc.code_block import CodeBlock

SAMPLE = Path(__file__).parent / 'sample_doc.py'


class TestParse(unittest.TestCase):
    def test_parse(self):
        blocks = parse(SAMPLE)

        self.assertEqual(
            [type(b) for b in blocks],
            [TextBlock, CodeBlock, TextBlock, CodeBlock, TextBlock, CodeBlock, ExpectedValueBlock],
        )

        # text block; opening ''' is not stored; ``` fence opens a code block
        self.assertEqual(blocks[0].lines, [
            '# Sample Documentation',
            '',
            'This module demonstrates all mddoc features.',
            '',
            'Here is some code:',
            '',
        ])

        # code inside the markdown fence
        self.assertEqual(blocks[1].lines, ['code inside text'])

        # text after the closing ``` up to the closing '''
        self.assertEqual(blocks[2].lines, ['', 'And some closing text.', '', "Now, let's compute:"])

        # code between the two doc-strings; define line is silently dropped
        self.assertEqual(blocks[3].lines, ['', 'x = 1 + 2', ''])

        # second text block (between """ delimiters)
        self.assertEqual(blocks[4].lines, ['The result should be:'])

        # blank line between the second """ and the validate call
        self.assertEqual(blocks[5].lines, [''])

        # validate call becomes an ExpectedValueBlock carrying the stored value
        self.assertEqual(blocks[6].variable_value, 3)
