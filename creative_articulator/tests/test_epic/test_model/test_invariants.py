import random
import shutil
import unittest
from pathlib import Path
from tempfile import mkdtemp

from creative_articulator.common import Node
from creative_articulator.epic.model import (
    Algorithms, CreativeArticulatorData, CreativeArticulatorLocations,
    CreativeArticulatorSettings, NodeData, NodeType, TextCache, verify, verify_against_loader
)

from .support import FakeLoader

NAMESPACES = ('creative_articulator.epic.model.basics',)
MAX_BLOCK_LENGTH = 200

WORDS = (
    'house forest letter door window silence morning rain shadow name '
    'road river stone hand voice answer question night table light'
).split()

EDGE_CASES = (
    '',
    '\n',
    '\n\n\n',
    '# Only a header',
    '# One\n## Two\n### Three',
    '***\n***\n***',
    'x' * 4000,
    'Line without a trailing newline',
    'Windows line ends\r\nand another one\r\n',
    '\tTab indented line, which is not a plan\nplain line',
    '# Заголовок\nТекст на другом языке.\n— Тире, — сказал он.\n',
    ' \n  \n   \n',
    'Text\n***',
    '#\n#\n#',
    'a\n' * 500,
)


def sentence(rng: random.Random) -> str:
    return ' '.join(rng.choice(WORDS) for _ in range(rng.randint(2, 14))).capitalize() + '.'


def line(rng: random.Random) -> str:
    kind = rng.choices(
        ('plain', 'dialog', 'blank', 'plan', 'header', 'separator'),
        weights=(50, 25, 12, 6, 5, 2)
    )[0]
    if kind == 'plain':
        return sentence(rng)
    if kind == 'dialog':
        return rng.choice(('-', '–', '—')) + ' ' + sentence(rng)
    if kind == 'blank':
        return ''
    if kind == 'plan':
        return ' ' * rng.randint(1, 4) + sentence(rng)
    if kind == 'header':
        return '#' * rng.randint(1, 3) + ' ' + sentence(rng)
    return '***'


def random_text(rng: random.Random) -> str:
    lines = [line(rng) for _ in range(rng.randint(1, 80))]
    return '\n'.join(lines) + ('\n' if rng.random() < 0.7 else '')


def edit(rng: random.Random, text: str) -> str:
    lines = text.split('\n')
    action = rng.choice(('insert', 'delete', 'replace', 'swap', 'append', 'truncate', 'duplicate'))
    if action == 'insert' or not lines:
        lines.insert(rng.randint(0, len(lines)), line(rng))
    elif action == 'delete':
        del lines[rng.randrange(len(lines))]
    elif action == 'replace':
        lines[rng.randrange(len(lines))] = line(rng)
    elif action == 'swap' and len(lines) > 1:
        i, j = rng.randrange(len(lines)), rng.randrange(len(lines))
        lines[i], lines[j] = lines[j], lines[i]
    elif action == 'append':
        lines.extend(line(rng) for _ in range(rng.randint(1, 10)))
    elif action == 'truncate':
        lines = lines[:rng.randrange(len(lines) + 1)]
    elif action == 'duplicate':
        start = rng.randrange(len(lines))
        stop = min(len(lines), start + rng.randint(1, 10))
        lines = lines[:stop] + lines[start:stop] + lines[stop:]
    return '\n'.join(lines)


class InvariantTestCase(unittest.TestCase):
    def setUp(self):
        self.folder = Path(mkdtemp())
        self.loader = FakeLoader()
        self.settings = CreativeArticulatorSettings(
            CreativeArticulatorLocations(self.folder),
            NAMESPACES,
            self.loader,
            Algorithms(max_block_length=MAX_BLOCK_LENGTH)
        )
        self.data = CreativeArticulatorData(Node(), self.settings)

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def assertSound(self, message: str = ''):
        problems = verify(self.data, MAX_BLOCK_LENGTH) + verify_against_loader(self.data)
        self.assertEqual([], problems, message)

    def blocks_by_id(self) -> dict[str, str]:
        return {
            node[NodeData].id: node[TextCache].text
            for node in self.data.root.descendants()
            if node[NodeData].node_type == NodeType.Block
        }


class TestEdgeCases(InvariantTestCase):
    def test_every_edge_case_is_split_soundly(self):
        for index, text in enumerate(EDGE_CASES):
            with self.subTest(text=text[:40]):
                self.loader.set_text(f'file-{index}', text)
                self.data.synchronize()
                self.assertSound(f'on {text[:40]!r}')

    def test_edge_cases_survive_a_reload(self):
        for index, text in enumerate(EDGE_CASES):
            self.loader.set_text(f'file-{index}', text)
        self.data.synchronize()
        reloaded = CreativeArticulatorData(Node(), self.settings)
        reloaded.load()
        self.assertEqual(
            {n[NodeData].id: n[TextCache].text for n in self.data.root.descendants()},
            {n[NodeData].id: n[TextCache].text for n in reloaded.root.descendants()}
        )


class TestRandomTexts(InvariantTestCase):
    ITERATIONS = 60

    def test_random_texts_are_split_soundly(self):
        rng = random.Random(20260811)
        for iteration in range(self.ITERATIONS):
            text = random_text(rng)
            with self.subTest(iteration=iteration):
                self.loader.set_text('file-1', text)
                self.data.update('file-1', text) if self.data.root.children else self.data.synchronize()
                self.assertSound(f'iteration {iteration}')

    def test_random_edits_are_applied_soundly(self):
        rng = random.Random(776)
        text = random_text(rng)
        self.loader.set_text('file-1', text)
        self.data.synchronize()
        for iteration in range(self.ITERATIONS):
            text = edit(rng, text)
            with self.subTest(iteration=iteration):
                self.loader.set_text('file-1', text)
                self.data.update('file-1', text)
                self.assertSound(f'iteration {iteration}')

    def test_synchronization_is_idempotent(self):
        rng = random.Random(4242)
        self.loader.set_text('file-1', random_text(rng))
        self.data.synchronize()
        for iteration in range(10):
            text = random_text(rng)
            self.loader.set_text('file-1', text)
            self.data.update('file-1', text)
            before = self.blocks_by_id()
            self.data.update('file-1', text)
            self.assertEqual(before, self.blocks_by_id(), f'iteration {iteration}')


class TestStability(InvariantTestCase):
    def test_untouched_blocks_keep_their_ids(self):
        rng = random.Random(99)
        text = random_text(rng)
        self.loader.set_text('file-1', text)
        self.data.synchronize()
        kept = 0
        touched = 0
        for _ in range(30):
            before = self.blocks_by_id()
            text = edit(rng, text)
            self.data.update('file-1', text)
            after = self.blocks_by_id()
            for id, block_text in before.items():
                if block_text in text:
                    touched += 1
                    kept += 1 if after.get(id) == block_text else 0
        self.assertGreater(kept / touched, 0.8, f'only {kept} of {touched} untouched blocks kept their id')

    def test_one_word_edit_disturbs_one_block(self):
        rng = random.Random(31337)
        self.loader.set_text('file-1', random_text(rng))
        self.data.synchronize()
        for iteration in range(10):
            text = random_text(rng).replace('house', 'hut')
            self.loader.set_text('file-1', text)
            self.data.update('file-1', text)
            before = self.blocks_by_id()
            edited = text.replace('hut', 'cottage', 1)
            if edited == text:
                continue
            self.data.update('file-1', edited)
            after = self.blocks_by_id()
            changed = [id for id in before if after.get(id) != before[id]]
            self.assertLessEqual(len(changed), 2, f'iteration {iteration}: {len(changed)} blocks disturbed')


if __name__ == '__main__':
    unittest.main()
