from kaia.avatar.dub.languages.en import *
from kaia.avatar.dub.core.algorithms import RegexpParser
from ..app.database import DiaryRecord
from datetime import datetime
import re
from nltk.stem import WordNetLemmatizer
import nltk





class FoodRecognizer:
    def __init__(self):
        self.float_parser = RegexpParser(Template("{amount}", amount=FloatDub()))
        self.wnl = WordNetLemmatizer()
        nltk.download('wordnet')

    def singularize(self, w):
        return self.wnl.lemmatize(w, 'n')

    def get_float_match(self, s):
        text_to_float_match = self.float_parser.longest_substring_match(s)
        if text_to_float_match is not None:
            amount = self.float_parser.match_to_values(text_to_float_match)['amount']
            return amount, text_to_float_match.span()[1]
        numeric_match = re.match('([\d.]+)', s)
        if numeric_match is not None:
            return float(numeric_match.group(0)), numeric_match.span()[1]
        return None, None

    def get_units_match(self, s):
        match = re.search('(\w+) of', s)
        if match is not None:
            return match.group(1), match.span()[1]
        return None, None


    def parse(self, s, time: datetime = datetime.now(), user: str|None = None):
        s = s[0].lower()+s[1:]
        s = s.strip()

        amount, right_of_amount = self.get_float_match(s)
        if amount is not None:
            s = s[right_of_amount:]
        else:
            amount = 1

        s = s.strip()
        unit, right_of_unit = self.get_units_match(s)
        if unit is not None:
            s = s[right_of_unit:]
            unit = self.singularize(unit)
        else:
            unit = 'portion'

        s = s.strip()
        s = re.sub('^(a |an |the )', '', s)
        s = s.strip()

        if len(s)==0:
            return None

        return DiaryRecord(user=user, timestamp=time, food=s, unit=unit, amount=amount)





