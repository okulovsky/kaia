import pickle
import unittest
from foundation_kaia.marshalling_2.marshalling.model.file import File
from foundation_kaia.marshalling_2.serialization import Serializer, SerializationContext


class TestFileSerializationRoundtrip(unittest.TestCase):

    def _roundtrip(self, file: File) -> File:
        s = Serializer.parse(File)
        ctx = SerializationContext()
        json_value = s.to_json(file, ctx)
        self.assertNotIn('@base64', str(json_value), "Serialization must not fall back to pickle")
        return s.from_json(json_value, ctx)

    def test_basic_roundtrip(self):
        original = File('test.wav', b'\x00\x01\x02\x03', File.Kind.Audio)
        result = self._roundtrip(original)
        self.assertEqual(original.name, result.name)
        self.assertEqual(original.content, result.content)
        self.assertEqual(original.kind, result.kind)

    def test_kind_guessed_from_name(self):
        original = File('audio.mp3', b'data')
        result = self._roundtrip(original)
        self.assertEqual(File.Kind.Audio, result.kind)

    def test_none_content(self):
        original = File('note.txt', None, File.Kind.Text)
        result = self._roundtrip(original)
        self.assertIsNone(result.content)

    def test_no_pickle_used(self):
        original = File('image.png', b'\x89PNG\r\n')
        s = Serializer.parse(File)
        ctx = SerializationContext()
        json_value = s.to_json(original, ctx)
        # Verify the JSON is plain dict, not a pickle blob
        self.assertIsInstance(json_value, dict)
        content_field = json_value.get('content')
        self.assertIsInstance(content_field, dict)
        self.assertEqual('bytes', content_field.get('@type'))


if __name__ == '__main__':
    unittest.main()
