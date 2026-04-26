# Table of contents

* [grammatron](#grammatron)
  * [Templates and Utterances](#templates-and-utterances)
    * [Multiple variables](#multiple-variables)
    * [Typed templates](#typed-templates)
  * [Dubs](#dubs)
    * [OptionsDub](#optionsdub)
    * [DateDub](#datedub)
    * [TimedeltaDub](#timedeltadub)
  * [Grammar](#grammar)
    * [PluralAgreement](#pluralagreement)
    * [German and Russian support](#german-and-russian-support)
    * [Multi-language templates](#multi-language-templates)

# grammatron

`grammatron` is a library for producing natural-language utterances from templates.
Instead of raw f-strings, templates use typed *dubs* (dubbing units) that convert
values into spoken-style text. Grammatron ensures the grammatical coherence of the
generated text in the supported languages, which are English, German and Russian.

## Templates and Utterances

A `Template` is built from an f-string that embeds `VariableDub` placeholders.
`CardinalDub` converts integers to their spoken form:

```python
from grammatron import Template, VariableDub, CardinalDub, DubParameters

AMOUNT = VariableDub("amount", CardinalDub())

template = Template(f"You've got {AMOUNT} messages")
```

Calling `template.utter(value)` (or the shorthand `template(value)`) produces an `Utterance`.
Call `.to_str()` to get the final string:

```python
result = template.utter(2).to_str()
```

The result will be:

```
"You've got two messages"
```

Pass `DubParameters(spoken=False)` to get the numeric form instead:

```python
result = template(3).to_str(DubParameters(spoken=False))
```

`result` will be:

```
"You've got 3 messages"
```

### Multiple variables

When a template has several dubs, pass assignments explicitly:

```python
UNREAD = VariableDub("unread", CardinalDub())

template = Template(f"You've got {AMOUNT} messages, {UNREAD} unread")
result = template(AMOUNT.assign(2), UNREAD.assign(1)).to_str()
```

The result will be:

```
"You've got two messages, one unread"
```

Keyword arguments are also supported:

```python
result = template(amount=2, unread=1).to_str()
```

The result will be:

```
"You've got two messages, one unread"
```

### Typed templates

Bind the template to a dataclass with `.with_type()` so a single object can be passed:

```python
from dataclasses import dataclass

@dataclass
class Data:
    amount: int
    unread: int

typed_template = Template(f"You've got {AMOUNT} messages, {UNREAD} unread").with_type(Data)

result = typed_template(Data(amount=2, unread=1)).to_str()
```

The result will be:

```
"You've got two messages, one unread"
```

## Dubs

A *dub* describes how to convert a value of certain type to a spoken and written string.
Several built-in dubs are available.

### OptionsDub

`OptionsDub` maps enum members (or plain strings) to their human-readable forms.
Enum names with underscores are automatically converted to space-separated words:

```python
from grammatron import VariableDub, Template, OptionsDub
from enum import Enum

class PaymentMethod(Enum):
    credit_card = 0
    paypal = "Paypal"

METHOD = VariableDub("method", OptionsDub(PaymentMethod))
template = Template(f"Your payment method is {METHOD}")

credit_card = template.to_str(PaymentMethod.credit_card)
paypal = template.to_str(PaymentMethod.paypal)
```

`credit_card` will be:

```
'Your payment method is credit card'
```

And for `paypal`:

```
'Your payment method is Paypal'
```

### DateDub

`DateDub` converts a `datetime` to its spoken form.
Use `.as_variable(name)` as a shorthand for wrapping in a `VariableDub`:

```python
import datetime
from grammatron import DateDub

template = Template(f"Today is {DateDub().as_variable('date')}")
result = template.to_str(datetime.datetime(2015, 1, 1))
```

`result` will be:

```
'Today is January, first, fifteenth'
```

### TimedeltaDub

```python
from grammatron import TimedeltaDub

template = Template(f"Now is {TimedeltaDub().as_variable('time')}")
result = template.to_str(datetime.timedelta(hours=15, minutes = 23))
```

`result` will be:

```
'Now is fifteen hours and twenty-three minutes'
```

## Grammar

### PluralAgreement

`PluralAgreement` wraps a numeric dub and a noun, producing the correctly inflected form:

```python
from grammatron import Template, VariableDub, CardinalDub, PluralAgreement

AMOUNT = VariableDub("amount", CardinalDub())
template = Template(f"You've got {PluralAgreement(AMOUNT, 'message')}")

result = template(1).to_str()
```

`result` will be:

```
"You've got one message"
```

```python
result = template(2).to_str()
```

And for 2:

```
"You've got two messages"
```

The noun argument can itself be a dub — the plural form of the chosen option is then used:

```python
from grammatron import OptionsDub

ITEM = VariableDub("item", OptionsDub(['car', 'bike', 'truck']))
template = Template(f"You've ordered {PluralAgreement(AMOUNT, ITEM)}")

cars = template.utter(AMOUNT.assign(2), ITEM.assign('car')).to_str()
bikes = template.utter(AMOUNT.assign(1), ITEM.assign('bike')).to_str()
```

`cars` will be:

```
"You've ordered two cars"
```

And for one bike:

```
"You've ordered one bike"
```

I will also work in fairly complicated cases:

```python
AMOUNT = VariableDub("amount", CardinalDub())
template = Template(f"You've ordered {PluralAgreement(AMOUNT, 'big glass of juice')}")
result = template(2).to_str()
```

The result will be:

```
"You've ordered two big glasses of juice"
```

However, this is not perfect:

```python
template = Template(f"You've ordered {PluralAgreement(AMOUNT, 'small glass of juice')}")
result = template(2).to_str()
```

The result will be:

```
"You've ordered two smalls glass of juice"
```

This happens because "small" can be used as the noun in English.

### German and Russian support

In germanic and slavic languages, this is more complicated: 

| English | German | Russian | 
--
I carry one small suitcase | Ich trage einen kleinen Koffer | Я несу один маленький чемодан
I travel with one small suitcase | Ich fahre mit einem kleinen Koffer | Я еду с одним маленьким чемоданом
I carry one small bag | Ich trage eine kleine Tasche | Я несу одну маленькую сумку
I travel with one small bag | Ich fahre mit einer kleinen Tasche | Я еду с одной маленькой сумкой
I carry two small suitcases | Ich trage zwei kleine Koffer | Я несу два маленьких чемодана 
I travel with two small suitcases | Ich fahre mit zwei kleinen Koffern | Я еду с двумя маленькими чемоданами
I carry two small bags | Ich trage zwei kleine Taschen | Я несу одну маленькую сумку
I traver with two small bags | Ich fahre mit zwei kleinen Taschen | Я еду с двумя маленькими сумками

So, to put correctly together a number and "kleine Tasche/klein Koffer" or "маленькая сумка/маленький чемодан", one must take into account:
* The case of the noun group ("tragen" and "нести" requires accusative, "fahre mit" - dative, "ехать" - prepositional case)
* The genus of the noun (Koffer and чемодан are mascular, Tasche and сумка are feminar, neutrum is also possible)
* The value of the numeral

These parameters determine the form of noun, adjective and the numeral. 
And this is not something you may ignore: natives see these errors instantly, and their impression of the product declines.

`grammatron` takes case of that too (but may fail in some cases, as it was with English):

```python
from grammatron import CardinalDub, PluralAgreement, OptionsDub, Template, DubParameters
from grammatron.grammars.de import DeCasus
from enum import Enum

class GermanOptions(Enum):
    bag = "kleine Tasche"
    suitcase = "klein Koffer"

AMOUNT = CardinalDub().as_variable("amount")
OBJECT = OptionsDub(GermanOptions).as_variable("object")
carry_template = Template(f"Ich trage {PluralAgreement(AMOUNT, OBJECT).grammar.de(casus=DeCasus.AKKUSATIV)}")
travel_template = Template(f"Ich fahre mit {PluralAgreement(AMOUNT, OBJECT).grammar.de(casus=DeCasus.DATIV)}")

results = [
    template.utter(amount = amount, object = object).to_str(DubParameters(language='de'))
    for amount in [1,2]
    for object in [GermanOptions.suitcase, GermanOptions.bag]
    for template in [carry_template, travel_template]
]
```

The results will be, as in the table above:

```
['Ich trage einen kleinen Koffer',
 'Ich fahre mit einem kleinen Koffer',
 'Ich trage eine kleine Tasche',
 'Ich fahre mit einer kleinen Tasche',
 'Ich trage zwei kleine Koffer',
 'Ich fahre mit zwei kleinen Koffern',
 'Ich trage zwei kleine Taschen',
 'Ich fahre mit zwei kleinen Taschen']
```

For russian:

```python
from grammatron.grammars.ru import RuCase

class RussianOptions(Enum):
    bag = "маленькая сумка"
    suitcase = "маленький чемодан"


AMOUNT = CardinalDub().as_variable("amount")
OBJECT = OptionsDub(RussianOptions).as_variable("object")
carry_template = Template(f"Я несу {PluralAgreement(AMOUNT, OBJECT).grammar.ru(case=RuCase.ACCUSATIVE)}")
travel_template = Template(f"Я еду с {PluralAgreement(AMOUNT, OBJECT).grammar.ru(case=RuCase.INSTRUMENTAL)}")

results = [
    template.utter(amount = amount, object = object).to_str(DubParameters(language='ru'))
    for amount in [1,2]
    for object in [RussianOptions.suitcase, RussianOptions.bag]
    for template in [carry_template, travel_template]
]

print(results)
```

### Multi-language templates

It is possible to declare multi-language templates:

```python
from grammatron import TimedeltaDub
TIME = TimedeltaDub().as_variable("time")
template = Template(
    f"It is {TIME}",
    de = f"Es ist {TIME}",
    ru = f"Сейчас {TIME}"
)
results = [
    template.utter(datetime.timedelta(hours=3,minutes=45)).to_str(DubParameters(language=language))
    for language in ['en', 'de', 'ru']
]
```

The results array is:

```
['It is three hours and forty-five minutes',
 'Es ist drei Stunden und fünfundvierzig Minuten',
 'Сейчас три часа и сорок пять минут']
```

Currently, this path is not well-explored, e.g., it's not compatible with OptionsDub.
Kaia evolved more in the direction where the LLM produces the translations to the different languages
instead of programmers writing them manually, so this branch of multi-language templates is unlikely to be resumed.