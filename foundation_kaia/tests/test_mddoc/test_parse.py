import unittest
from pathlib import Path
from foundation_kaia.mddoc import parse
from foundation_kaia.mddoc.doc_block import TextBlock, ExpectedValueBlock
from foundation_kaia.mddoc.code_block import CodeBlock

SAMPLE = Path(__file__).parent / 'sample_doc.py'


class TestParse(unittest.TestCase):
    def test_parse(self):
        blocks = parse(SAMPLE)

        self.assertEqual(
            [type(b) for b in blocks],
            [CodeBlock, ExpectedValueBlock, CodeBlock, TextBlock, CodeBlock, TextBlock, CodeBlock],
        )

        # code before the validate call; define line is silently dropped
        self.assertEqual(blocks[0].lines, [
            'from foundation_kaia.mddoc import ControlValue',
            '',
            'x = 1 + 2',
        ])

        # validate call becomes an ExpectedValueBlock carrying the stored value
        self.assertEqual(blocks[1].variable_value, 3)

        # blank line between the validate call and the opening '''
        self.assertEqual(blocks[2].lines, [''])

        # text block; opening ''' and closing ``` are not stored in any block
        self.assertEqual(blocks[3].lines, [
            '# Sample Documentation',
            '',
            'This module demonstrates all mddoc features.',
            '',
            'Here is some code:',
            '',
        ])

        # code inside the markdown fence
        self.assertEqual(blocks[4].lines, ['code inside text'])

        # text after the closing ```
        self.assertEqual(blocks[5].lines, ['', 'And some closing text.'])

        # code after the closing '''
        self.assertEqual(blocks[6].lines, ['', 'y = 10'])
