from brainbox.deciders import Zonos, EspeakPhonemizer

_REPlACEMENTS = {
    '"': '“”«»„',
    "'": '‘’`',
    '-': '–—−'
}

ENGLISH_PHONEMES = [
        'ɪ', 'n', 's', 't', 'k', 'ə', 'ɹ', 'l', 'd', 'm', 'æ', 'ɛ', 'z', 'p', 'b',
        'eɪ', 'ɑː', 'ɚ', 'oʊ', 'f', 'iː', 'aɪ', 'i', 'ᵻ', 'ɡ', 'ŋ', 'uː', 'v', 'ɾ',
        'ʃ', 'ʌ', 'dʒ', 'h', 'ɐ', 'əl', 'w', 'j', 'ɜː', 'ɑːɹ', 'tʃ', 'iə', 'θ', 'ɔː',
        'aʊ', 'oːɹ', 'ɔːɹ', 'ʊ', 'ɔ', 'oː', 'ɔɪ', 'ʊɹ', 'ɛɹ', 'ɪɹ', 'ʒ', 'aɪɚ', 'ð',
        'aɪə', 'ʔ', 'n̩'
    ]

def english():
    from .language import Language
    return Language(
        name='en',
        words_symbols=set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'"),
        typographic_replacements=_REPlACEMENTS,
        native_espeak_phonemes=set(ENGLISH_PHONEMES),
        sample_text=(
            "The geopolitical situation is now worsening and we have seen a hike in terms of the crude prices.",
            "Then they wait on another set of outdoor benches after clearing the security check.",
            "Observers say talks are the only way forward because both nuclear-armed countries have much to lose.",
            "It is the same stocks that we are holding and buying more of, which I have spoken about many times.",
            "Gymnastics gave her superior body awareness, while competing in triathlons built up her endurance.",
        )
    )
