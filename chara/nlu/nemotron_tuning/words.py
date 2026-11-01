"""
Made-up words and the phrases with them, to teach and to test Nemotron on words it has never heard.

A word follows the syllables of its language and is not in the given vocabulary. A phrase is a carrier of a skill
with a slot, and the slot gets one of three groups of words:
    control: an ordinary word, the normal level of errors;
    names:   the long names the testbed fails on;
    new:     a made-up word, the test words are never in the training set.
The difference between the groups shows what an unknown word does to itself and to the words around it.

No heavy imports, as in manifest.py.
"""
import random
from dataclasses import dataclass

LANGUAGES = ('en', 'de', 'ru')
GROUPS = ('control', 'names', 'new')
NAME, THING, PLACE = 'name', 'thing', 'place'

_SYLLABLES = ((2, 3), (3, 4), (4, 3), (5, 1))  # (syllables in a word, weight)
_CODA_SHARE = 0.2
_COMPLEX_SHARE = 0.15  # consonant clusters and long vowels are rare, the words stay easy to pronounce

_ONSETS = {
    'en': ('b d f g h j k l m n p r s t v w z'.split(), 'bl br cl cr dr fl fr gl gr pl pr sk sl sm sn sp st tr ch sh th'.split()),
    'de': ('b d f g h j k l m n p r s t w z'.split(), 'br dr fl fr gl gr kl kr pl schl schm schn schw sp st tr'.split()),
    'ru': ('б в г д з к л м н п р с т ф х ш'.split(), 'бр вр гр др кр пр тр ст ск зв кл пл'.split()),
}
_VOWELS = {
    'en': ('a e i o u'.split(), 'ai ee oo ou'.split()),
    'de': ('a e i o u'.split(), 'ä ö ü ei au eu ie'.split()),
    'ru': ('а о у и е'.split(), ('я', 'ю')),
}
_CODAS = {
    'en': 'n r l m s t k'.split(),
    'de': 'n r l m s t ch'.split(),
    'ru': 'н р л м с т к'.split(),
}
# Russian made-up words take the endings of the slot, as "добавь мумзики", "свет в бербараточной"
_ENDINGS = {
    'en': {NAME: ('a', 'o', 'i', 'an', 'en', 'on'), THING: ('ies', 'ers', 'os'), PLACE: ('ery', 'ory', 'arium')},
    'de': {NAME: ('a', 'o', 'i', 'an', 'en', 'on'), THING: ('e', 'en', 'chen'), PLACE: ('chen', 'ment', 'um')},
    'ru': {NAME: ('а', 'о', 'и', 'у', 'е'), THING: ('ики', 'ушки', 'ята'), PLACE: ('очной', 'альной', 'арной')},
}
_LOWERCASE = {('en', THING), ('en', PLACE), ('ru', THING), ('ru', PLACE)}

NAMES = {
    'en': ('Naruto', 'Kirishima', 'Uroraka', 'Yaoyorozu', 'Todoroki', 'Aomine', 'Kagami'),
    'de': ('Naruto', 'Kirishima', 'Uroraka', 'Yaoyorozu', 'Todoroki', 'Aomine', 'Kagami'),
    'ru': ('Наруто', 'Кирисима', 'Урорака', 'Яойорозу', 'Тодороки', 'Аомине', 'Кагами'),
}


@dataclass(frozen=True)
class Skill:
    kind: str
    carriers: tuple[str, ...]
    # Ordinary words in the form the carriers need
    control: tuple[str, ...]


SKILLS = {
    'en': {
        'call': Skill(NAME, (
            'Call {word}', 'Dial {word}', 'Phone {word}', 'Ring {word}', 'Call up {word}', 'Give {word} a call',
            'Can you call {word} for me?', 'Could you dial {word}?', 'Get {word} on the line', 'Connect me with {word}',
            "Let's give {word} a call.", 'Please call {word}',
        ), ('Anna', 'John', 'Peter', 'Mary', 'David', 'Emma', 'Michael')),
        'meeting': Skill(NAME, (
            'Remind me about the meeting with {word}', 'Set up a meeting with {word} tomorrow',
            'When is my meeting with {word}?', 'Cancel the meeting with {word}', 'Remind me to talk to {word}',
        ), ('Anna', 'John', 'Peter', 'Mary', 'David', 'Emma', 'Michael')),
        'shopping': Skill(THING, (
            'Add {word} to the shopping list', 'Put {word} on my shopping list', 'Buy {word}',
            "Don't forget to buy {word}", 'We need {word}, add it to the list',
        ), ('milk', 'bread', 'eggs', 'butter', 'cheese', 'apples', 'coffee')),
        'room': Skill(PLACE, (
            'Turn off the light in the {word}', 'Turn on the light in the {word}', 'Switch off the light in the {word}',
            'Make the light brighter in the {word}', 'Close the window in the {word}',
        ), ('kitchen', 'bedroom', 'bathroom', 'living room', 'hallway', 'garage', 'basement')),
    },
    'de': {
        'call': Skill(NAME, (
            'Ruf {word} an', 'Ruf bitte {word} an', 'Ruf mal {word} an', 'Ruf {word} für mich an',
            'Kannst du {word} anrufen?', 'Ich möchte {word} anrufen', 'Verbinde mich mit {word}', '{word} anrufen, bitte',
            'Wähle {word} für mich', 'Ruf {word} sofort an',
        ), ('Anna', 'Peter', 'Thomas', 'Maria', 'Stefan', 'Julia', 'Michael')),
        'meeting': Skill(NAME, (
            'Erinnere mich an das Treffen mit {word}', 'Plane ein Treffen mit {word} für morgen',
            'Wann ist mein Treffen mit {word}?', 'Sag das Treffen mit {word} ab', 'Erinnere mich, mit {word} zu sprechen',
        ), ('Anna', 'Peter', 'Thomas', 'Maria', 'Stefan', 'Julia', 'Michael')),
        'shopping': Skill(THING, (
            'Setz {word} auf die Einkaufsliste', 'Schreib {word} auf die Einkaufsliste', 'Kauf {word}',
            'Vergiss nicht, {word} zu kaufen', 'Wir brauchen {word}, schreib das auf die Liste',
        ), ('Milch', 'Brot', 'Eier', 'Butter', 'Käse', 'Äpfel', 'Kaffee')),
        'room': Skill(PLACE, (
            'Mach das Licht im {word} aus', 'Mach das Licht im {word} an', 'Schalte das Licht im {word} ein',
            'Mach das Licht im {word} heller', 'Schließ das Fenster im {word}',
        ), ('Schlafzimmer', 'Badezimmer', 'Wohnzimmer', 'Flur', 'Keller', 'Büro', 'Kinderzimmer')),
    },
    'ru': {
        'call': Skill(NAME, (
            'Позвони {word}', 'Набери {word}', 'Позвони {word} прямо сейчас', 'Позвони {word}, пожалуйста.',
            'Набери {word}, давай быстрее!', 'Набери {word}, пожалуйста.', 'Позвони, пожалуйста, {word}.',
            'Сделай звонок {word}, пожалуйста.', 'Позвони {word} сейчас', 'Позвони {word} по телефону',
        ), ('маме', 'папе', 'Ивану', 'Анне', 'Сергею', 'Ольге', 'брату')),
        'meeting': Skill(NAME, (
            'Напомни о встрече с {word}', 'Напомни мне про встречу с {word}', 'Поставь встречу с {word} на завтра',
            'Когда у меня встреча с {word}?', 'Отмени встречу с {word}', 'Свяжись с {word} по телефону',
        ), ('Иваном', 'Анной', 'Сергеем', 'Ольгой', 'директором', 'врачом', 'бабушкой')),
        'shopping': Skill(THING, (
            'Добавь {word} в список покупок', 'Запиши {word} в список покупок', 'Купи {word}',
            'Не забудь купить {word}', 'Нужно купить {word}, запиши в список',
        ), ('молоко', 'хлеб', 'яйца', 'масло', 'сыр', 'яблоки', 'кофе')),
        'room': Skill(PLACE, (
            'Выключи свет в {word}', 'Включи свет в {word}', 'Погаси свет в {word}',
            'Сделай свет ярче в {word}', 'Закрой окно в {word}',
        ), ('кухне', 'спальне', 'ванной', 'гостиной', 'прихожей', 'детской', 'кладовке')),
    },
}


def _pick(parts: tuple[list, ...], rnd: random.Random) -> str:
    simple, complex_ = parts
    return rnd.choice(complex_ if rnd.random() < _COMPLEX_SHARE else simple)


def made_up_word(language: str, kind: str, rnd: random.Random) -> str:
    syllables = rnd.choices([s for s, _ in _SYLLABLES], [w for _, w in _SYLLABLES])[0]
    word = ''
    for _ in range(syllables - 1):
        word += _pick(_ONSETS[language], rnd) + _pick(_VOWELS[language], rnd)
        if rnd.random() < _CODA_SHARE:
            word += rnd.choice(_CODAS[language])
    word += _pick(_ONSETS[language], rnd) + rnd.choice(_ENDINGS[language][kind])
    return word if (language, kind) in _LOWERCASE else word.capitalize()


def made_up_words(language: str, kind: str, count: int, rnd: random.Random, known: set[str]) -> list[str]:
    """`count` different words, none of them in `known` (lowercase). The words are added to `known`."""
    words = []
    while len(words) < count:
        word = made_up_word(language, kind, rnd)
        if word.lower() not in known:
            known.add(word.lower())
            words.append(word)
    return words


def _phrase(language: str, skill: str, group: str, carrier: str, word: str) -> dict:
    return dict(text=carrier.format(word=word), word=word, group=group, skill=skill, language=language)


def phrases(language: str, group: str, count: int, rnd: random.Random, known: set[str]) -> list[dict]:
    """`count` phrases, evenly over the skills that can take the words of `group`. New words are added to `known`."""
    skills = SKILLS[language]
    names = [s for s in skills if group != 'names' or skills[s].kind == NAME]
    result = []
    for index in range(count):
        name = names[index % len(names)]
        skill = skills[name]
        if group == 'control':
            word = skill.control[index // len(names) % len(skill.control)]
        elif group == 'names':
            word = NAMES[language][index // len(names) % len(NAMES[language])]
        else:
            word = made_up_words(language, skill.kind, 1, rnd, known)[0]
        result.append(_phrase(language, name, group, rnd.choice(skill.carriers), word))
    return result
