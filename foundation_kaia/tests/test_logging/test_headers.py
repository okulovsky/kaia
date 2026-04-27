from unittest import TestCase
from foundation_kaia.logging import Logger
from foundation_kaia.logging.simple import HeaderItem

class TestHeaders(TestCase):
    def test_headers(self):
        logger = Logger()
        data = []
        with logger.with_callback(data.append):
            with logger.section("Section 1"):
                with logger.section("Section 1.1"):
                    pass
                with logger.section("Section 1.2"):
                    pass


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

