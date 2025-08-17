from unittest import TestCase
from chara.voice_clone.sentences.corpus_filter.dictionary_filter import DictionaryFilter
from chara.tools import Language
from foundation_kaia.misc import Loc
from yo_fluq import *

class DictionaryFilterTestCase(TestCase):
    def test_dictionary(self):
        with Loc.create_test_file() as file:
            FileIO.write_text('[un#k] 2\nabbuchtet 1788\nabbuchung 1789', file)
            s = DictionaryFilter.process_vosk_dictionary(file, Language.German().standardizer)
            self.assertEqual({'abbuchung', 'abbuchtet'}, s)
            f = DictionaryFilter(Language.German().standardizer, s)
            self.assertIsNone(f.filter("test abbuchung"))
            self.assertEqual(f.filter("abbuchung abbuchtet"), "abbuchung abbuchtet")