# Copyright 2022 David Scripka. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Derived from openwakeword/data.py, Apache-2.0, David Scripka (2022).
# Pinned source revision: 368c03716d1e92591906a84949bc477f3a834455.
import logging
import re
from pathlib import Path

import numpy as np
import pronouncing
from openwakeword.data import phoneme_replacement


def generate_adversarial_texts(
    input_text: str,
    N: int,
    include_partial_phrase: float = 0,
    include_input_words: float = 0,
    phonemizer_path=None,
):
    """
    Generate adversarial words and phrases based on phoneme overlap.
    Currently only works for english texts.
    Note that homophones are excluded, as this wouldn't actually be an adversarial example for the input text.

    Args:
        input_text (str): The target text for adversarial phrases
        N (int): The total number of adversarial texts to return. Uses sampling,
                 so not all possible combinations will be included and some duplicates
                 may be present.
        include_partial_phrase (float): The probability of returning a number of words less than the input
                                        text (but always between 1 and the number of input words)
        include_input_words (float): The probability of including individual input words in the adversarial
                                     texts when the input text consists of multiple words. For example,
                                     if the `input_text` was "ok google", then setting this value > 0.0
                                     will allow for adversarial texts like "ok noodle", versus the word "ok"
                                     never being present in the adversarial texts.

    Returns:
        list: A list of strings corresponding to words and phrases that are phonetically similar (but not identical)
              to the input text.
    """
    # Get phonemes for english vowels (CMUDICT labels)
    vowel_phones = [
        "AA",
        "AE",
        "AH",
        "AO",
        "AW",
        "AX",
        "AXR",
        "AY",
        "EH",
        "ER",
        "EY",
        "IH",
        "IX",
        "IY",
        "OW",
        "OY",
        "UH",
        "UW",
        "UX",
    ]

    word_phones = []
    input_text_phones = [pronouncing.phones_for_word(i) for i in input_text.split()]

    # Download phonemizer model for OOV words, if needed
    if [] in input_text_phones:
        if phonemizer_path is None or not Path(phonemizer_path).is_file():
            raise ValueError("DeepPhonemizer checkpoint missing; run make setup")
        phonemizer_mdl_path = str(phonemizer_path)

        # Create phonemizer object
        from dp.phonemizer import Phonemizer

        phonemizer = Phonemizer.from_checkpoint(phonemizer_mdl_path)

    for phones, word in zip(input_text_phones, input_text.split()):
        if phones != []:
            word_phones.extend(phones)
        elif phones == []:
            logging.getLogger(__name__).warning(
                f"The word '{word}' was not found in the pronunciation dictionary! "
                "Using the DeepPhonemizer library to predict the phonemes."
            )
            phones = phonemizer(word, lang="en_us")
            logging.getLogger(__name__).warning(f"Phones for '{word}': {phones}")
            word_phones.append(re.sub(r"[\]|\[]", "", re.sub(r"\]\[", " ", phones)))
        elif isinstance(phones[0], list):
            logging.getLogger(__name__).warning(
                f"There are multiple pronunciations for the word '{word}'."
            )
            word_phones.append(phones[0])

    # add all possible lexical stresses to vowels
    word_phones = [
        re.sub(
            "|".join(vowel_phones),
            lambda x: str(x.group(0)) + "[0|1|2]",
            re.sub(r"\d+", "", i),
        )
        for i in word_phones
    ]

    adversarial_phrases = []
    for phones, word in zip(word_phones, input_text.split()):
        query_exps = []
        phones = phones.split()
        adversarial_words = []
        if len(phones) <= 2:
            query_exps.append(" ".join(phones))
        else:
            query_exps.extend(
                phoneme_replacement(
                    phones, max_replace=max(0, len(phones) - 2), replace_char="(.){1,3}"
                )
            )

        for query in query_exps:
            matches = pronouncing.search(query)
            matches_phones = [pronouncing.phones_for_word(i)[0] for i in matches]
            allowed_matches = [
                i for i, j in zip(matches, matches_phones) if j != phones
            ]
            adversarial_words.extend([i for i in allowed_matches if word.lower() != i])

        if adversarial_words != []:
            adversarial_phrases.append(adversarial_words)

    # Build combinations for final output
    adversarial_texts = []
    for i in range(N):
        txts = []
        for j, k in zip(adversarial_phrases, input_text.split()):
            if np.random.random() > (1 - include_input_words):
                txts.append(k)
            else:
                txts.append(np.random.choice(j))

        if (
            include_partial_phrase is not None
            and len(input_text.split()) > 1
            and np.random.random() <= include_partial_phrase
        ):
            n_words = np.random.randint(1, len(input_text.split()) + 1)
            adversarial_texts.append(
                " ".join(np.random.choice(txts, size=n_words, replace=False))
            )
        else:
            adversarial_texts.append(" ".join(txts))

    # Remove any exact matches to input phrase
    adversarial_texts = [i for i in adversarial_texts if i != input_text]

    return adversarial_texts


def generate_negative_texts(settings, resources, count):
    import random

    from .resources import ResourceInstaller

    paths = ResourceInstaller(settings.resource_folder).paths(resources)
    random.seed(settings.seed)
    np.random.seed(settings.seed)
    result = list(settings.custom_negative_phrases)
    for text in settings.target_variants:
        result.extend(
            generate_adversarial_texts(
                text,
                max(1, count // len(settings.target_variants)),
                include_partial_phrase=1.0,
                include_input_words=0.2,
                phonemizer_path=paths.get("phonemizer_path"),
            )
        )
    targets = {s.strip().casefold() for s in settings.target_variants}
    return [s for s in result if s.strip() and s.strip().casefold() not in targets]
