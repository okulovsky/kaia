from grammatron.dubs.core.parser_intructions import *
from grammatron.dubs import IDub, DubParameters, TemplateDub
from dataclasses import dataclass


def escape(s):
    s = s.lower().replace('-', ' ')
    disable = set(',.?!')
    return ''.join(c for c in s if c not in disable)

@dataclass
class KaldiGrammarBuilder:
    instruction: IParserInstruction
    variables: dict[tuple[str,...], VariableInfo]
    root_dub: IDub
    parameters: DubParameters|None = None

    lines: tuple[str]|None = None

    def next(self, instruction):
        return KaldiGrammarBuilder(
            instruction,
            self.variables,
            self.root_dub,
            self.parameters
        )

    def build(self):
        for method in [self.on_constant, self.on_variable, self.on_sequence, self.on_union]:
            result = method()
            if result is not None:
                self.lines = result
                break
        if self.lines is None:
            raise ValueError(f"Instruction {self.instruction} cannot be processed")

        return self


    def cartesian(self, set1, set2):
        return tuple(l1 + l2 for l1 in set1 for l2 in set2)


    def on_constant(self):
        if isinstance(self.instruction, ConstantParserInstruction):
            return (escape(self.instruction.value),)

    def to_variable_name(self, path: tuple[str,...]) -> str:
        return '___'.join(path)


    def on_variable(self):
        if isinstance(self.instruction, VariableParserInstruction):
            var_name = self.to_variable_name(self.instruction.variable_name)
            return (f'<{var_name}>{{{var_name}}}', )

    def on_sequence(self):
        if isinstance(self.instruction, SequenceParserInstruction):
            lines = ('',)
            for item in self.instruction.sequence:
                builder = self.next(item).build()
                lines = self.cartesian(lines, builder.lines)

            return lines

    def on_union(self):
        if isinstance(self.instruction, UnionParserInstruction):
            is_simple = True
            simple_strings = []
            for u in self.instruction.union:
                if not isinstance(u, ConstantParserInstruction):
                    is_simple = False
                    break
                else:
                    simple_strings.append(u.value)
            if is_simple:
                alternatives = '('+'|'.join(escape(s) for s in simple_strings)+')'
                return (alternatives,)
            alternatives = []
            for u in self.instruction.union:
                builder = self.next(u).build()
                alternatives.extend(builder.lines)
            return tuple(alternatives)

    def to_rule(self, name: str):
        lines = [f'[{name}]']
        for key, value in self.variables.items():
            lines.append(self.to_variable_name(key)+' = '+'|'.join(v for v in value.string_values_to_value))
        for l in self.lines:
            lines.append(l)
        return '\n'.join(lines)


    def parse(self, recognition):
        to_convolute = {}
        for e in recognition['entities']:
            variable_path = tuple(e['entity'].split('___'))
            value = e['value']
            true_value = self.variables[variable_path].string_values_to_value[value]
            to_convolute[variable_path] = true_value

        return self.root_dub.convolute_values(to_convolute, self.parameters)

    @staticmethod
    def make_all(dub: TemplateDub):
        parse_data = dub.get_parser_data()
        new_variables = {}
        for key, variable_info in parse_data.variables.items():
            new_svv = {}
            for str_value, value in variable_info.string_values_to_value.items():
                new_svv[escape(str_value)] = value
            new_variables[key] = VariableInfo(new_svv)
        builder = KaldiGrammarBuilder(parse_data.root, new_variables, dub).build()
        return builder

