"""Invents Parler voice descriptions, so that a corpus is not spoken by one person.

Parler takes the voice as a sentence of English rather than as a speaker id, which is what
makes it usable here: the diversity a wake word model needs can be *described* instead of
being collected, and nothing is drawn from a fixed roster. The wording is not free-form,
though. The descriptions Parler was trained on were written by binning measured properties
of each recording into a ladder of phrases -- "slightly low-pitched", "at a moderate speed",
"very close-sounding" -- and the model follows those far more reliably than synonyms of
them. The vocabulary below stays on that ladder, and every voice is a fresh combination of
it rather than a named speaker.

Two things are deliberately not varied.

Emotion, because it is not an axis of the installed model. mini-v1 was annotated for pitch,
rate, monotony, reverberation and noise and for nothing else, so "angry" or "happy" is out of
distribution for it and comes back as noise on the axes that do exist. What stands in for it
is expressivity: very monotone through to very expressive and animated. (Emotion is real in
parler-tts-mini-expresso, but that model knows four speakers, which is the opposite of what
is wanted here.)

Noise, because the noise the detector has to survive is the kitchen's, and that is mixed in
afterwards from real recordings. Asking Parler for it too would put synthetic noise under
real noise and make the crop harder for no gain. Distance *is* varied: someone calling from
across the room is real, and no amount of mixing recovers it.
"""

import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DescriptionVocabulary:
    """The phrasings Parler actually responds to, and how to assemble them."""

    kinds: tuple[str, ...]
    pitches: tuple[str, ...]
    speeds: tuple[str, ...]
    expressivity: tuple[str, ...]
    reverberation: tuple[str, ...]
    quality: tuple[str, ...]
    templates: tuple[str, ...]


# Only "male" and "female" were in the annotations -- they came out of a gender classifier,
# which had no other labels to give. The rest are extrapolation: the description is read by a
# language model, so they are understood as English rather than ignored, but they are not
# properties the acoustic model was taught to vary. They are kept in, and kept a minority, so
# the corpus gains if they work without being ruined if they do not.
_KINDS = (
    "male",
    "male",
    "male",
    "female",
    "female",
    "female",
    "young male",
    "young female",
    "old male",
    "old female",
    "androgynous",
)

_PITCHES = (
    "very low-pitched",
    "low-pitched",
    "slightly low-pitched",
    "moderately pitched",
    "slightly high-pitched",
    "high-pitched",
    "very high-pitched",
)
_SPEEDS = (
    "very slowly",
    "slowly",
    "slightly slowly",
    "at a moderate speed",
    "slightly quickly",
    "quickly",
    "very quickly",
)
_EXPRESSIVITY = (
    "very monotone",
    "monotone",
    "slightly expressive and animated",
    "expressive and animated",
    "very expressive and animated",
)
_REVERBERATION = (
    "very close-sounding",
    "close-sounding",
    "slightly close-sounding",
    "slightly distant-sounding",
    "distant-sounding",
    "very distant-sounding",
)
# The model card asks for this phrase by name for the cleanest output, and clean is what is
# wanted: everything dirty about the final clip is added afterwards, on purpose.
_QUALITY = ("very clear", "very clear", "very clear", "quite clear")

# No template names anyone. A name pins the timbre to one of the twenty voices the model
# renders consistently, which is a roster -- and a roster is what is being avoided.
_TEMPLATES = (
    (
        "{article} {kind} speaker with {a_pitch} voice delivers {possessive} words {speed}. "
        "The recording is {reverberation}, with {quality} audio."
    ),
    (
        "In {an_expressivity} voice, {article} {kind} speaker pronounces the words {speed}. "
        "The voice is {pitch}, and the recording is {reverberation}, with {quality} audio."
    ),
    (
        "{article} {kind} speaker, {pitch} and {expressivity}, delivers {possessive} words "
        "{speed}. The recording is {reverberation}, with {quality} audio."
    ),
    (
        "The speaker is {kind}, with {a_pitch}, {expressivity} voice, and pronounces "
        "{possessive} words {speed}. The recording is {reverberation}, with {quality} audio."
    ),
    (
        "{article} {kind} voice, {pitch} and {expressivity}, says the words {speed} "
        "in {a_reverberation} recording with {quality} audio."
    ),
)


PARLER = DescriptionVocabulary(
    kinds=_KINDS,
    pitches=_PITCHES,
    speeds=_SPEEDS,
    expressivity=_EXPRESSIVITY,
    reverberation=_REVERBERATION,
    quality=_QUALITY,
    templates=_TEMPLATES,
)


def _article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


@dataclass
class VoiceDescriptionGenerator:
    """Turns one integer into one voice.

    The seed is the whole identity of the voice: it picks the description, and it is also
    what Parler is handed as its sampling seed, so the same integer gives the same speaker
    twice. That is what makes a generated corpus reproducible without storing anything --
    a clip is described by the number that made it.
    """

    vocabulary: DescriptionVocabulary = field(default_factory=lambda: PARLER)

    def describe(self, voice_seed: int | None = None) -> str:
        vocabulary = self.vocabulary
        generator = random.Random(voice_seed)

        kind = generator.choice(vocabulary.kinds)
        pitch = generator.choice(vocabulary.pitches)
        expressivity = generator.choice(vocabulary.expressivity)
        reverberation = generator.choice(vocabulary.reverberation)

        description = generator.choice(vocabulary.templates).format(
            article=_article(kind),
            kind=kind,
            pitch=pitch,
            a_pitch=f"{_article(pitch)} {pitch}",
            speed=generator.choice(vocabulary.speeds),
            expressivity=expressivity,
            an_expressivity=f"{_article(expressivity)} {expressivity}",
            reverberation=reverberation,
            a_reverberation=f"{_article(reverberation)} {reverberation}",
            quality=generator.choice(vocabulary.quality),
            possessive=self._possessive(kind),
        )
        return description[:1].upper() + description[1:]

    @staticmethod
    def _possessive(kind: str) -> str:
        if "female" in kind:
            return "her"
        if "male" in kind:
            return "his"
        return "their"
