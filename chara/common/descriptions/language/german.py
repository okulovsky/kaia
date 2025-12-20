from .upsampling_dataset.german import de_upsampling_datset

GERMAN_PHONEMES = [
    'n', 'ə', 't', 'l', 'ɾ', 'a', 's', 'ɛ', 'ɪ', 'f', 'k', 'ɡ', 'r', 'm', 'b', 'ʃ', 'iː', 'd',
    'eː', 'ɜ', 'ʊ', 'p', 'oː', 'aɪ', 'ts', 'ɑː', 'v', 'z', 'ŋ', 'ɔ', 'ç', 'h', 'uː', 'aʊ', 'y',
    'ɑ', 'j', 'x', 'ɛː', 'yː', 'ɔø', 'øː', 'œ', '??', 'pf']

def german():
    from .language import Language
    return Language(
        name = 'de',
        words_symbols= set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÖÜäöüß'),
        native_espeak_phonemes=set(GERMAN_PHONEMES),
        sample_text = (
            'Es ist absehbar, dass große Teile des chinesischen Automarktes für die deutsche Autoindustrie auf Dauer verloren sind.',
            'Staatliche Unterstützung ist allenfalls in Form von zeitlich limitierten Schutzzöllen ökonomisch sinnvoll.',
            'Es soll einen Schlagabtausch geben, so viel verspricht zumindest der Titel des Formats.',
            'Von einer fairen Gesprächssituation ist die Sendung ohnehin weit entfernt.',
            'Allerdings ist der Zuseher nach der Sendung nicht viel schlauer als zuvor.',
        ),
        upsampling_dataset_reader=de_upsampling_datset
    )
