import os
from pathlib import Path
from rhasspyserver_hermes.train import sentences_to_graph
from rhasspyasr_kaldi.train import train, LanguageModelType
import rhasspynlu
from collections import defaultdict
from utils import kaldi_path, profile_path

class Trainer:
    def __init__(self,
                 path: Path,
                 sentences: str,
                 language: str,
                 custom_words: str = '',
                 ):
        self.path = path
        self.sentences = sentences
        self.custom_words = custom_words
        self.language = language


    def _build_and_save_graph(self):
        graph, slot_replacements = sentences_to_graph(
            sentences_dict={str(self.path / 'sentences.ini'): self.sentences},
            slots_dirs=[
                self.path / 'slots',
                profile_path / self.language/'slots',
            ],
            slot_programs_dirs=[
                self.path / 'slot_programs',
                profile_path / self.language/'slot_programs',
            ],
            language='en',
            word_transform=str.lower
        )

        with open(self.path / 'intent_graph.pickle.gz', 'wb') as file:
            rhasspynlu.graph_to_gzip_pickle(graph, file)

        return graph

    def _get_pronunciations(self):
        custom_words_path = self.path/'kaldi_custom_words.txt'
        with open(custom_words_path, 'w', encoding='utf-8') as file:
            file.write(self.custom_words)

        dictionaries = [
            self.path / 'kaldi/base_dictionary.txt',
            custom_words_path,
        ]
        pronunciations = defaultdict(list)

        for dict_path in dictionaries:
            with open(dict_path, "r", encoding='utf-8') as base_dict_file:
                dict_content = {}
                rhasspynlu.g2p.read_pronunciations(base_dict_file, word_dict=dict_content)
                for word in dict_content:
                    pronunciations[word].extend(dict_content[word])

        return pronunciations

    def _get_frequent_words(self):
        with open(profile_path / self.language/'frequent_words.txt', 'r', encoding='utf-8') as file:
            frequent_words = [s.strip() for s in file][:100]
        return frequent_words


    def train(self):
        for key, value in ENVS.items():
            os.environ[key] = value

        train(
            graph=self._build_and_save_graph(),
            pronunciations=self._get_pronunciations(),
            model_dir=self.path / 'kaldi/model',
            graph_dir=self.path / 'kaldi/model/graph',
            dictionary=self.path / 'kaldi/dictionary.txt',
            language_model=self.path / 'kaldi/language_model.txt',
            dictionary_word_transform=str.lower,
            g2p_model=self.path / 'kaldi/g2p.fst',
            g2p_word_transform=None,
            missing_words_path=self.path / 'kaldi_unknown_words.txt',
            vocab_path=None,
            language_model_fst=None,
            base_language_model_fst=self.path / 'kaldi/base_language_model.fst',
            base_language_model_weight=0,
            mixed_language_model_fst=self.path / 'kaldi/mixed.fst',
            balance_counts=True,
            kaldi_dir=kaldi_path,
            language_model_type=LanguageModelType.TEXT_FST,
            spn_phone='SPN',
            sil_phone='SIL',
            eps='<eps>',
            allow_unknown_words=False,
            frequent_words=self._get_frequent_words(),
            unk='<unk>',
            sil='<sil>',
            unk_nonterm='#nonterm:unk',
            unk_prob=1e-05,
            sil_prob=0.5,
            unknown_token='<unk>',
            max_unk_words=8,
            cancel_word='',
            cancel_prob=0.01
        )

        unknown_words = {}
        with open(self.path/'kaldi_unknown_words.txt', encoding='utf-8') as file:
            for line in file:
                try:
                    first_space = line.index(' ')
                except ValueError:
                    pass
                unknown_words[line[:first_space].strip()] = line[first_space:].strip()
        return dict(status='OK', unknown_words=unknown_words)



ENVS = {
    'SUPERVISOR_GROUP_NAME': 'speech_to_text',
    'HOSTNAME': '6c46571adf40',
    'RHASSPY_PROFILE_DIR': '/profiles/en',
    'PWD': '/',
    'HOME': '/',
    'LANG': 'C.UTF-8',
    'VIRTUAL_ENV': '/usr/lib/rhasspy/.venv',
    'KALDI_DIR': '/usr/lib/rhasspy/.venv/lib/kaldi',
    'PYTHONPATH': '/usr/lib/rhasspy/rhasspy-asr-kaldi-hermes:/usr/lib/rhasspy:/usr/lib/rhasspy/rhasspy-wake-snowboy-hermes:/usr/lib/rhasspy/rhasspy-wake-raven-hermes:/usr/lib/rhasspy/rhasspy-wake-raven:/usr/lib/rhasspy/rhasspy-wake-precise-hermes:/usr/lib/rhasspy/rhasspy-wake-porcupine-hermes:/usr/lib/rhasspy/rhasspy-wake-pocketsphinx-hermes:/usr/lib/rhasspy/rhasspy-tts-wavenet-hermes:/usr/lib/rhasspy/rhasspy-tts-larynx-hermes:/usr/lib/rhasspy/rhasspy-tts-cli-hermes:/usr/lib/rhasspy/rhasspy-supervisor:/usr/lib/rhasspy/rhasspy-speakers-cli-hermes:/usr/lib/rhasspy/rhasspy-snips-nlu-hermes:/usr/lib/rhasspy/rhasspy-snips-nlu:/usr/lib/rhasspy/rhasspy-silence:/usr/lib/rhasspy/rhasspy-server-hermes:/usr/lib/rhasspy/rhasspy-remote-http-hermes:/usr/lib/rhasspy/rhasspy-rasa-nlu-hermes:/usr/lib/rhasspy/rhasspy-profile:/usr/lib/rhasspy/rhasspy-nlu-hermes:/usr/lib/rhasspy/rhasspy-nlu:/usr/lib/rhasspy/rhasspy-microphone-pyaudio-hermes:/usr/lib/rhasspy/rhasspy-microphone-cli-hermes:/usr/lib/rhasspy/rhasspy-homeassistant-hermes:/usr/lib/rhasspy/rhasspy-hermes:/usr/lib/rhasspy/rhasspy-fuzzywuzzy-hermes:/usr/lib/rhasspy/rhasspy-fuzzywuzzy:/usr/lib/rhasspy/rhasspy-dialogue-hermes:/usr/lib/rhasspy/rhasspy-asr-vosk-hermes:/usr/lib/rhasspy/rhasspy-asr-pocketsphinx-hermes:/usr/lib/rhasspy/rhasspy-asr-pocketsphinx:/usr/lib/rhasspy/rhasspy-asr-kaldi-hermes:/usr/lib/rhasspy/rhasspy-asr-kaldi:/usr/lib/rhasspy/rhasspy-asr-deepspeech-hermes:/usr/lib/rhasspy/rhasspy-asr-deepspeech:/usr/lib/rhasspy/rhasspy-asr:',
    'TERM': 'xterm',
    'RHASSPY_PROFILE': 'en',
    'SHLVL': '2',
    'APP_DIR': '/usr/lib/rhasspy',
    'LD_LIBRARY_PATH': '/usr/lib/rhasspy/.venv/lib:',
    'SUPERVISOR_PROCESS_NAME': 'speech_to_text',
    'PATH': '/usr/lib/rhasspy/rhasspy-wake-snowboy-hermes/bin:/usr/lib/rhasspy/rhasspy-wake-raven-hermes/bin:/usr/lib/rhasspy/rhasspy-wake-precise-hermes/bin:/usr/lib/rhasspy/rhasspy-wake-porcupine-hermes/bin:/usr/lib/rhasspy/rhasspy-wake-pocketsphinx-hermes/bin:/usr/lib/rhasspy/rhasspy-tts-wavenet-hermes/bin:/usr/lib/rhasspy/rhasspy-tts-larynx-hermes/bin:/usr/lib/rhasspy/rhasspy-tts-cli-hermes/bin:/usr/lib/rhasspy/rhasspy-speakers-cli-hermes/bin:/usr/lib/rhasspy/rhasspy-snips-nlu-hermes/bin:/usr/lib/rhasspy/rhasspy-server-hermes/bin:/usr/lib/rhasspy/rhasspy-remote-http-hermes/bin:/usr/lib/rhasspy/rhasspy-rasa-nlu-hermes/bin:/usr/lib/rhasspy/rhasspy-nlu-hermes/bin:/usr/lib/rhasspy/rhasspy-microphone-pyaudio-hermes/bin:/usr/lib/rhasspy/rhasspy-microphone-cli-hermes/bin:/usr/lib/rhasspy/rhasspy-homeassistant-hermes/bin:/usr/lib/rhasspy/rhasspy-fuzzywuzzy-hermes/bin:/usr/lib/rhasspy/rhasspy-dialogue-hermes/bin:/usr/lib/rhasspy/rhasspy-asr-vosk-hermes/bin:/usr/lib/rhasspy/rhasspy-asr-pocketsphinx-hermes/bin:/usr/lib/rhasspy/rhasspy-asr-kaldi-hermes/bin:/usr/lib/rhasspy/rhasspy-asr-deepspeech-hermes/bin:/usr/lib/rhasspy/.venv/bin:/usr/lib/rhasspy/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
    'RHASSPY_BASE_DIR': '/usr/lib/rhasspy',
    'DEBIAN_FRONTEND': 'noninteractive',
    'SUPERVISOR_ENABLED': '1',
    '_': '/usr/lib/rhasspy/.venv/bin/python3'
}
