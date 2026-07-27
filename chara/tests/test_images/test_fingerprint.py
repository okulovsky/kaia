from unittest import TestCase
from chara.images.common import ImageFingerprint, ImageSetupFingerprint, ThemeFingerprint


class ImageFingerprintTagsTestCase(TestCase):
    def test_flattens_all_set_fields(self):
        fingerprint = ImageFingerprint(
            ImageSetupFingerprint('Miku', ThemeFingerprint(
                location='forest',
                season='summer',
                weather='sunny',
                time_of_day='dusk',
                special_day='halloween',
            )),
            'cooking',
        )
        self.assertEqual(
            dict(
                character='Miku',
                activity='cooking',
                location='forest',
                season='summer',
                weather='sunny',
                time_of_day='dusk',
                special_day='halloween',
            ),
            fingerprint.to_tags(),
        )

    def test_omits_unset_theme_fields(self):
        fingerprint = ImageFingerprint(
            ImageSetupFingerprint('Miku', ThemeFingerprint(location='forest')),
            'cooking',
        )
        self.assertEqual(
            dict(character='Miku', activity='cooking', location='forest'),
            fingerprint.to_tags(),
        )

    def test_no_theme_fields_set(self):
        fingerprint = ImageFingerprint(ImageSetupFingerprint('Miku', ThemeFingerprint()), 'cooking')
        self.assertEqual(dict(character='Miku', activity='cooking'), fingerprint.to_tags())
