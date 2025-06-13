from ...core import IDub, DubParameters, ParserData
from .regex_builder import BuilderForParserInstruction
from dataclasses import dataclass

@dataclass
class RegexParserData:
    builder: BuilderForParserInstruction
    dub: IDub
    parameters: DubParameters
    parser_data: ParserData

def regex_parser_data(dub: IDub, parameters: DubParameters):
    parser_data = dub.get_parser_data(parameters)
    builder = BuilderForParserInstruction(parser_data.root, parser_data.variables).build()
    return RegexParserData(
        builder,
        dub,
        parameters,
        parser_data
    )

class RegexParser:
    def __init__(self, dub: IDub, parameters: DubParameters|None = None):
        self.data: RegexParserData = dub.get_cached_value(regex_parser_data, parameters)

    def parse(self, s: str):
        value = self.data.builder.parse(s)
        return self.data.dub.convolute_values(value, self.data.parameters)
