import unittest

from creative_articulator.epic.ai.background import Summarization
from creative_articulator.epic.ai.writing.case import SelectionCase
from creative_articulator.epic.ai.writing.writing_ai import WritingAi
from creative_articulator.epic.model import ParagraphType
from chara.common.llm import LLMSetup, MockLLMEngine

from .test_case.support import EXAMPLE, initialize


BEFORE_HEADER = 'Краткое содержание романа до этого места'
AFTER_HEADER = 'Краткое содержание романа после этого места'
BLOCK_TEXT_HEADER = 'Текст блока романа'


class TestWritingAiExpandPrompt(unittest.TestCase):
    def setUp(self):
        self.init = initialize(EXAMPLE)
        self.addCleanup(self.init.tmp.cleanup)
        self.file_node = self.init.file_node
        self.file_node[Summarization] = Summarization('summary of the whole file')
        self.file_node.children[0][Summarization] = Summarization('summary of the first section')
        self.init.blocks[3][Summarization] = Summarization('summary of the preceding block')
        self.file_node.children[3][Summarization] = Summarization('summary of the following section')
        # blocks[4] (the block the selection lands in) is left without a
        # summary on purpose, to check it is skipped.
        self.case = SelectionCase.parse(
            self.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )
        self.writing_ai = WritingAi(LLMSetup(MockLLMEngine(), 'mock-model'))
        self.prompt = self.writing_ai.build_prompt(self.case, WritingAi.Expand)

    def _section(self, start_marker: str, end_marker: str) -> str:
        start = self.prompt.index(start_marker)
        end = self.prompt.index(end_marker, start)
        return self.prompt[start:end]

    def test_before_section_has_left_sibling_and_parent_summaries(self):
        section = self._section(BEFORE_HEADER, AFTER_HEADER)
        self.assertIn('summary of the first section', section)
        self.assertIn('summary of the preceding block', section)
        self.assertIn('summary of the whole file', section)

    def test_after_section_has_right_sibling_summary_but_not_parent(self):
        section = self._section(AFTER_HEADER, BLOCK_TEXT_HEADER)
        self.assertIn('summary of the following section', section)
        self.assertNotIn('summary of the whole file', section)

    def test_current_block_text_and_selection_are_present(self):
        self.assertIn('1st paragraph of the third block', self.prompt)
        self.assertIn(self.case.selection.text, self.prompt)

    def test_plan_format_explanation_is_always_present(self):
        self.assertIn('Формат плана', self.prompt)


class TestWritingAiExpandPromptWithPlanSelection(unittest.TestCase):
    def setUp(self):
        self.init = initialize('''
Alpha
^  Do the thing$
   Do the other thing
Beta''')
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )
        self.writing_ai = WritingAi(LLMSetup(MockLLMEngine(), 'mock-model'))
        self.prompt = self.writing_ai.build_prompt(self.case, WritingAi.Expand)

    def test_selection_is_a_plan_line(self):
        self.assertTrue(self.case.selection.paragraphs.has_type(ParagraphType.Plan))
        self.assertEqual(1, len(self.case.selection.paragraphs))

    def test_indent_of_the_selected_line_is_reported(self):
        self.assertIn('отступ — 2 пробел(ов)', self.prompt)

    def test_indent_expected_from_the_sub_items_is_reported(self):
        self.assertIn('больше: 3 пробел(ов)', self.prompt)


class TestWritingAiActions(unittest.TestCase):
    def setUp(self):
        self.init = initialize('''
Alpha
^ Do the thing$
Beta''')
        self.addCleanup(self.init.tmp.cleanup)
        self.case = SelectionCase.parse(
            self.init.file_node,
            self.init.before_selection,
            self.init.selection,
            self.init.after_selection,
        )
        self.writing_ai = WritingAi(LLMSetup(MockLLMEngine(), 'mock-model'))

    def test_unknown_action_in_build_prompt(self):
        with self.assertRaises(ValueError):
            self.writing_ai.build_prompt(self.case, 'whatever')

    def test_unknown_action_in_run(self):
        with self.assertRaises(ValueError):
            self.writing_ai.run('prompt', 'whatever')


if __name__ == '__main__':
    unittest.main()
