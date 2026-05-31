# German Grammar Module — Implementation Plan

## Files to create in `grammatron/grammars/de/`

### `categories.py`
Enums for German grammatical categories:
- `DeCasus` — NOMINATIV, GENITIV, DATIV, AKKUSATIV
- `DeGenus` — MASKULINUM, FEMININUM, NEUTRUM
- `DeNumerus` — SINGULAR, PLURAL
- `DeArticleType` — STRONG (no article), WEAK (after *der/die/das*), MIXED (after *ein/kein/mein*)

---

### `word_tools.py`
Class `DeWordTools`:

- **Noun lookup** via `german_nouns` — given a word, returns the full flexion dict and genus (`m`/`f`/`n`). `german_nouns` is a full declension dictionary, so it has all forms directly — no generation needed. `simplemma` is used only as a fallback to get the base form of words not found directly (e.g. "Hunden" → "Hund", then look up "Hund").
- **Adjective lemma** via `simplemma` — gets the base stem for adjective inflection (e.g. `"roten"` → `"rot"`).
- **`is_noun(word)`** — checks `german_nouns`; if the word or its simplemma lemma appears as a `Substantiv` with non-empty flexion, it's a noun.
- **`is_adjective_in_base_form(word)`** — `simplemma.lemmatize(word) == word` AND the word is not a noun.

---

### `declinator.py`
Class `DeDeclinator` (naming: "Declinator for De language"):

**Nouns** — look up word (or its simplemma lemma) in `german_nouns`, map `(DeCasus, DeNumerus)` to a key like `"genitiv singular"`, return that form. Falls back to original word if not found.

**Adjectives** — hard-coded 3 tables (strong / weak / mixed), indexed by `(DeNumerus, DeGenus, DeCasus)` → suffix string. Get stem via `simplemma`, append suffix.

Adjective ending tables:

**Strong** (no article):
```
              Masc    Fem     Neut    Plural
Nom:          -er     -e      -es     -e
Gen:          -es     -er     -es     -er
Dat:          -em     -er     -em     -en
Akk:          -en     -e      -es     -e
```

**Weak** (after der/die/das):
```
              Masc    Fem     Neut    Plural
Nom:          -e      -e      -e      -en
Gen:          -en     -en     -en     -en
Dat:          -en     -en     -en     -en
Akk:          -en     -e      -en     -en
```

**Mixed** (after ein/kein/mein):
```
              Masc    Fem     Neut    Plural
Nom:          -er     -e      -es     -en
Gen:          -en     -en     -en     -en
Dat:          -en     -en     -en     -en
Akk:          -en     -e      -es     -en
```

**`choose_words_to_inflect(words)`** — implements the rule: *take all adjectives (in base form) that precede the first noun, plus the first noun itself*. Walk words left-to-right; collect words where `DeWordTools.is_adjective_in_base_form(w)` is true; when the first noun is found via `DeWordTools.is_noun(w)`, append it and stop. This correctly handles "kleine Gurke mit dem Sosse" → inflect ["kleine", "Gurke"] and skip everything after "Gurke".

**`declinate(text, casus, genus, numerus, article_type)`** — splits text into word/non-word fragments via `WordProcessor`, selects words via `choose_words_to_inflect`, inflects each one (noun or adjective), joins back. Also **prepends the article** when needed:
- STRONG → no article
- WEAK → prepend definite article (der/die/das/die) for the correct casus/genus/numerus
- MIXED + SINGULAR → prepend indefinite article (ein/eine/ein) for the correct casus/genus
- MIXED + PLURAL → no article, use STRONG adjective endings (grammatically correct absence)

Genus for the article is auto-detected from the first noun found in the phrase via `german_nouns`; the explicitly-set genus in the grammar rule overrides this.

Definite article table (WEAK):
```
         Masc    Fem     Neut    Plural
Nom:     der     die     das     die
Gen:     des     der     des     der
Dat:     dem     der     dem     den
Akk:     den     die     das     die
```

Indefinite article table (MIXED, singular only):
```
         Masc    Fem     Neut
Nom:     ein     eine    ein
Gen:     eines   einer   eines
Dat:     einem   einer   einem
Akk:     einen   eine    ein
```

Note: `DeWordTools.is_noun` is used for word type detection, so no external POS library needed. `german_nouns` dictionary is the POS source for nouns; anything in base form that isn't a noun is treated as an adjective.

---

### `grammar_rule.py`
Class `DeGrammarRule(GrammarRule)`:
- Constructor: `(casus=None, genus=None, numerus=None, article_type=None)` — all optional
- `merge_with_lower_priority` — fills in `None` fields from the lower-priority rule
- `to_correct_form` — calls `DeDeclinator.declinate(text, ...)`; only applies to `OptionsDub`, `GrammarAdoptableDub`, `ToStrDub`
- `all_morphological_forms` — iterates all combinations of `DeCasus × DeNumerus × DeGenus × DeArticleType`, returns deduplicated set of all generated forms

---

### `plural_agreement.py`
Class `DePluralAgreement(IPluralAgreement)`:
- German numeral agreement: amount == 1 → nominativ singular; everything else → nominativ plural
- Outer grammar rule's casus/article_type is passed through to both the amount and the entity

---

### `__init__.py`
Exports `DeCasus`, `DeGenus`, `DeNumerus`, `DeArticleType`, `DeGrammarRule`, `DePluralAgreement`.

---

## Files to modify

**`grammars/grammar_setter.py`** — add `de(casus=None, genus=None, numerus=None, article_type=None)` method; add `'de'` branch to `get_default_grammar_for_language`.

**`grammars/__init__.py`** — add `from .de import *`.

**`grammars/common/word_processor.py`** — extend `WORD_PATTERN` regex to include `äöüÄÖÜß`.

**`requirements.txt` and `pyproject.toml`** — add `simplemma`, `german_nouns` (no spacy — avoids model download, not container-friendly).

---

## Globalization (`grammatron/globalization/`)

Add German support to all language-dispatching dubs:

**`plural_agreement.py`** — add `de=DePluralAgreement(amount, entity)`

**`month_dub.py`** — add German month names:
Januar, Februar, März, April, Mai, Juni, Juli, August, September, Oktober, November, Dezember

**`weekday_dub.py`** — add German weekday names:
Montag, Dienstag, Mittwoch, Donnerstag, Freitag, Samstag, Sonntag

**`date_dub.py`** — add German date patterns, e.g.:
- `"der {DAY}. {MONTH}"` (nominative)
- `"am {DAY}. {MONTH}"` (dative, with article)
- `"der {DAY}. {MONTH} {YEAR}"`

**`timedelta_dub.py`** — add `de` entry to `WORD_TO_LANGUAGE` and `CONJ`:
- hours → `Stunde`, minutes → `Minute`, seconds → `Sekunde`; conjunction → `und`

**`year_dub.py`** — add `de` sequence (German year is read the same as English ordinally, no special grammar needed beyond the ordinal form).

---

## Tests to create in `grammatron/tests/test_grammar/test_de/`

Model after `tests/test_grammar/test_ru/test_declinator/test_declinator.py`:

**`test_declinator.py`**:
- Single noun declension: `"Hund"` → `"Hundes"` (genitiv singular)
- Single noun plural: `"Haus"` → `"Häuser"` (nominativ plural)
- Adjective + noun phrase: `"kleine Gurke"` → `"kleinen Gurke"` (akkusativ singular femininum, weak)
- Phrase with words after noun: `"kleine Gurke mit dem Sosse"` → only first two words change
- Adjective strong declension: `"frischer Kaffee"` → various cases
- Fall back for unknown word (word not in `german_nouns`): returns unchanged

**`test_plural_agreement.py`**:
- Model after `test_ru/test_plural_agreement.py`: test amount=1 (singular) and amount>1 (plural) with `DePluralAgreement`
