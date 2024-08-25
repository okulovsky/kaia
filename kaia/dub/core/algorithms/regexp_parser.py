from typing import *
import re
from .to_ini import IniRuleRecord, ToIni
from .values_convolutor import ValuesConvolutor


class RegexpParser:
    def __init__(self, template):
        self.template = template
        rule = ToIni().walk(template.dub)
        self.closed_regexes = tuple(RegexpParser.ini_record_to_regex(r, True) for r in rule.records)
        self.open_regexes = tuple(RegexpParser.ini_record_to_regex(r, False) for r in rule.records)


    def match(self, s):
        match = None
        for parser in self.closed_regexes:
            match = parser.match(s)
            if match is not None:
                break
        if match is None:
            raise ValueError(f'String `{s}` cannot be parsed')
        return match

    def longest_substring_match(self, s):
        winner_match = None
        for regex in self.open_regexes:
            match = regex.search(s)
            if match is None:
                continue
            if winner_match is None:
                winner_match = match
                continue
            if match.span()[1] - match.span()[0] > winner_match.span()[1] - winner_match.span()[0]:
                winner_match = match
        return winner_match

    def match_to_values(self, match):
        return ValuesConvolutor(match.groupdict()).walk(self.template.dub)

    def parse(self, s):
        match = self.match(s)
        if match is None:
            raise ValueError(f"Cannot parse string `{s}` with template {self.template.name}")
        return self.match_to_values(match)


    @staticmethod
    def ini_record_to_regex(record: IniRuleRecord, close):
        line = []
        if close:
            line.append('^')
        for c in record.content:
            if c.constant is not None:
                line.append(re.escape(c.constant))
            elif c.alternatives is not None:
                line.append('(' + '|'.join(re.escape(a) for a in c.alternatives) + ')')
            elif c.variable is not None:
                line.append('(?P<' + c.variable + '>' + '|'.join(re.escape(v) for v in record.headers[c.variable]) + ')')
        if close:
            line.append('$')
        line = ''.join(line)
        r = re.compile(line)
        return r
