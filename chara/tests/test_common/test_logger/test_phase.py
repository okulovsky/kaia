from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common import FileCache, Logger, LineItem, HeaderItem, ExceptionItem


class PhaseTestCase(TestCase):
    def test_success(self):
        logger = Logger(print)
        with Loc.create_test_folder() as folder:
            item = FileCache()
            item.initialize(folder/'test')

            @logger.phase(item)
            def _():
                logger.log("Starting doing something")
                item.write("RESPONSE")
                logger.log("Finished doing something")

            @logger.phase(item)
            def _():
                raise ValueError("Should not be here")

            data = logger.items

            self.assertEqual(len(data), 8)

            # 1
            self.assertIsInstance(data[0], HeaderItem)
            self.assertEqual(data[0].level, 0)
            self.assertEqual(data[0].caption, "test")

            # 2
            self.assertIsInstance(data[1], LineItem)
            self.assertEqual(data[1].text, "Starting doing something")

            # 3
            self.assertIsInstance(data[2], LineItem)
            self.assertEqual(data[2].text, "Finished doing something")

            # 4
            self.assertIsInstance(data[3], LineItem)
            self.assertEqual(data[3].text, "Stage test completed in 0 seconds")

            # 5
            self.assertIsInstance(data[4], HeaderItem)
            self.assertEqual(data[4].level, 0)
            self.assertEqual(data[4].caption, "test")

            # 6
            self.assertIsInstance(data[5], LineItem)
            self.assertEqual(data[5].text, "Stage restored from cache")

            # 7
            self.assertIsInstance(data[6], LineItem)
            self.assertEqual(data[6].text, "Starting doing something")

            # 8
            self.assertIsInstance(data[7], LineItem)
            self.assertEqual(data[7].text, "Finished doing something")

    def test_failure(self):
        logger = Logger(print)
        with Loc.create_test_folder() as folder:
            item = FileCache()
            item.initialize(folder/'test')

            with self.assertRaises(ValueError):
                @logger.phase(item)
                def _():
                    raise ValueError("Exception")
                    item.write("RESPONSE")

            data = logger.items
            self.assertEqual(len(data), 4)

            # 1
            self.assertIsInstance(data[0], HeaderItem)
            self.assertEqual(data[0].level, 0)
            self.assertEqual(data[0].caption, "test")

            # 2
            self.assertIsInstance(data[1], ExceptionItem)
            self.assertIsInstance(data[1].exception, ValueError)
            self.assertEqual(str(data[1].exception), "Exception")

            self.assertIsInstance(data[2], LineItem)
            self.assertEqual(data[2].text, "Can't save phase log to disk")
            # 4
            self.assertIsInstance(data[3], LineItem)
            self.assertEqual(data[3].text, "Stage test failed in 0 seconds")
