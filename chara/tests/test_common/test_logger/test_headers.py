from unittest import TestCase
from chara.common import Logger
from chara.common import HeaderItem

class TestHeaders(TestCase):
    def test_headers(self):
        logger = Logger(print)
        with logger.section("Section 1"):
            with logger.section("Section 1.1"):
                pass
            with logger.section("Section 1.2"):
                pass
        data = logger.items

        self.assertEqual(len(data), 3)

        # 1
        self.assertIsInstance(data[0], HeaderItem)
        self.assertEqual(data[0].level, 0)
        self.assertEqual(data[0].caption, "Section 1")

        # 2
        self.assertIsInstance(data[1], HeaderItem)
        self.assertEqual(data[1].level, 1)
        self.assertEqual(data[1].caption, "Section 1.1")

        # 3
        self.assertIsInstance(data[2], HeaderItem)
        self.assertEqual(data[2].level, 1)
        self.assertEqual(data[2].caption, "Section 1.2")

