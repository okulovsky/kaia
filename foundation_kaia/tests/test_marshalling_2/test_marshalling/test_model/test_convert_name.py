import unittest
from foundation_kaia.marshalling_2.marshalling.model.service_model import convert_name


class TestConvertName(unittest.TestCase):

    def test_plain_camel(self):
        self.assertEqual(convert_name('MyService'), 'my-service')

    def test_leading_i_uppercase(self):
        self.assertEqual(convert_name('IMyService'), 'my-service')

    def test_trailing_interface(self):
        self.assertEqual(convert_name('MyServiceInterface'), 'my-service')

    def test_leading_i_and_trailing_interface(self):
        self.assertEqual(convert_name('IMyServiceInterface'), 'my-service')

    def test_leading_i_lowercase_not_stripped(self):
        # 'Io' — second char is lowercase, should NOT strip the I
        self.assertEqual(convert_name('IoService'), 'io-service')

    def test_single_word(self):
        self.assertEqual(convert_name('Service'), 'service')

    def test_single_capital_i_word(self):
        # Just 'I' alone — no second char, should not strip
        self.assertEqual(convert_name('I'), 'i')

    def test_multiple_humps(self):
        self.assertEqual(convert_name('MyBigService'), 'my-big-service')

    def test_already_lowercase(self):
        self.assertEqual(convert_name('service'), 'service')

    def test_abbreviation(self):
        self.assertEqual(convert_name('TortoiseTTS'), 'tortoise-tts')


if __name__ == '__main__':
    unittest.main()
