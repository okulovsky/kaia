from phonemizer.backend import EspeakBackend
from phonemizer.punctuation import Punctuation
from phonemizer.separator import Separator
import json

def phonemize():
    with open('/data/phonemizer.input.json', 'r') as file:
        lines = json.load(file)

    backend = EspeakBackend('en-us')
    separator = Separator(phone='/', word=' ')
    result = backend.phonemize(lines, separator=separator, strip=True)

    with open('/data/phonemizer.output.json', 'w') as file:
        json.dump(result, file)


