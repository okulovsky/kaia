from ...core.parser_intructions import *
import regex
from dataclasses import dataclass

def get_group_name(var_path, index):
    return '___'.join(var_path)+'__'+str(index)


@dataclass
class BuilderForParserInstruction:
    instruction: IParserInstruction
    variables: dict[tuple[str, ...], VariableInfo]

    is_root: bool = True
    var_counts: dict[tuple[str, ...], int] = field(default_factory=dict)
    subdomain_group_name_to_subdomain_builder: dict[str, 'BuilderForParserInstruction'] = field(default_factory=dict)
    iteration_group_name_to_iteration_capture: dict[str, str] = field(default_factory=dict)
    indent: int = 0
    with_variables_names: bool = True


    regex_string: str|None = None
    resulting_group_name: str|None = None
    subdomain_type: str|None = None
    pattern: regex.Pattern|None = None


    def next(self, instruction: IParserInstruction):
        return BuilderForParserInstruction(
            instruction,
            self.variables,
            False,
            self.var_counts,
            self.subdomain_group_name_to_subdomain_builder,
            self.iteration_group_name_to_iteration_capture,
            self.indent+1,
            self.with_variables_names
        )



    def build(self) -> 'BuilderForParserInstruction':
        for method in [self.on_constant,self.on_variable,self.on_sequence,self.on_union,
                       self.on_subdomain,self.on_iteration]:
            result = method()
            if result is None:
                continue
            if isinstance(result,str):
                self.regex_string = result
                break
            if isinstance(result, tuple):
                self.regex_string = result[0]
                self.resulting_group_name = result[1]
                break
        if self.regex_string is None:
            raise ValueError(f"Unexpected instruction type {type(self.instruction)}")
        if self.is_root:
            try:
                self.pattern = regex.compile(self.regex_string, regex.VERBOSE)
            except Exception as ex:
                raise ValueError("Error when building regex\n"+self.regex_string) from ex
        return self


    @property
    def INDENT(self):
        return "    "*self.indent



    def on_constant(self):
        if isinstance(self.instruction, ConstantParserInstruction):
            return self.INDENT + regex.escape(self.instruction.value)

    def variable_to_group_name(self, variable_name):
        count = self.var_counts.get(variable_name, 0)
        self.var_counts[variable_name] = count + 1
        group_name = get_group_name(variable_name, count)
        return group_name

    def on_variable(self):
        if isinstance(self.instruction, VariableParserInstruction):
            if self.instruction.variable_name not in self.variables:
                raise ValueError(f"Variable {self.instruction.variable_name} not found")

            if self.with_variables_names:
                group_prefix = f'?P<{self.variable_to_group_name(self.instruction.variable_name)}>'
            else:
                group_prefix = '?:'

            var_info = self.variables[self.instruction.variable_name]
            options = "|".join(
                regex.escape(v) for v in var_info.string_values_to_value
            )
            return f"{self.INDENT}({group_prefix}{options})"

    def on_sequence(self):
        if isinstance(self.instruction, SequenceParserInstruction):
            parts = [
                self.next(part).build().regex_string
                for part in self.instruction.sequence
            ]
            return f"{self.INDENT}(?:\n" + f"\n".join(parts) + f"\n{self.INDENT})"

    def on_union(self):
        if isinstance(self.instruction, UnionParserInstruction):
            parts = [
                self.next(part).build().regex_string
                for part in self.instruction.union
            ]
            sep = f"\n{self.INDENT}|\n"
            return f"{self.INDENT}(?:\n" + sep.join(parts) + f"\n{self.INDENT})"

    def on_subdomain(self):
        if isinstance(self.instruction, SubdomainInstruction):
            group_name = self.variable_to_group_name(self.instruction.variable_name)

            subdomain_builder = BuilderForParserInstruction(
                self.instruction.subdomain.root,
                self.instruction.subdomain.variables
            ).build()

            self.subdomain_group_name_to_subdomain_builder[group_name] = subdomain_builder

            no_varname_builder = self.next(self.instruction.subdomain.root)
            no_varname_builder.variables = self.instruction.subdomain.variables
            no_varname_builder.with_variables_names = False
            no_varname_builder.subdomain_group_name_to_subdomain_builder = {}
            no_varname_builder.iteration_group_name_to_iteration_capture = {}

            regex = no_varname_builder.build().regex_string
            return regex, group_name

    def on_iteration(self):
        if isinstance(self.instruction, IterationParserInstruction):
            inner = self.next(self.instruction.iterated).build()
            if inner.resulting_group_name is None:
                raise ValueError("Inside iteration, only subdomain is acceptable")
            self.subdomain_group_name_to_subdomain_builder[inner.resulting_group_name].subdomain_type='iteration'
            if self.with_variables_names:
                group_prefix = f'?P<{inner.resulting_group_name}>'
                iteration_capture = f'{inner.resulting_group_name}__iteration_capture'
                self.iteration_group_name_to_iteration_capture[inner.resulting_group_name] = iteration_capture
                capture_prefix = f'?P<{iteration_capture}>'
            else:
                group_prefix = '?:'
                capture_prefix = ''
            return f"{self.INDENT}({capture_prefix}({group_prefix}\n" + inner.regex_string + f"\n{self.INDENT})*)"

    def parse(self, s: str):
        if not self.is_root:
            raise ValueError("Only the root can be used for parsing")
        if self.pattern is None:
            raise ValueError("Builder probably was not built")
        if not isinstance(s, str):
            raise ValueError(f"Expected str, but was: {s}")
        match = self.pattern.fullmatch(s)
        if match is None:
            raise ValueError(f'String `{s}` cannot be matched with the pattern:{self.regex_string}')

        capture_dict = match.capturesdict()
        result = {}
        for variable, count in self.var_counts.items():
            for index in range(count):
                key = get_group_name(variable, index)
                if key not in capture_dict:
                    continue
                if len(capture_dict[key]) == 0:
                    capture_key = self.iteration_group_name_to_iteration_capture.get(key, None)
                    if capture_key is None:
                        continue
                    if len(capture_dict[capture_key]) == 0:
                        continue

                value = capture_dict[key]
                if key in self.subdomain_group_name_to_subdomain_builder:
                    subdomain = self.subdomain_group_name_to_subdomain_builder[key]
                    if subdomain.subdomain_type == 'iteration':
                        if not isinstance(value, list):
                            raise ValueError(f"For key {key} (variable {variable}), the subdomain with iteration is set, that requires list of strings as a value, but the value vas `{value}`")
                        result[variable] = [subdomain.parse(element) for element in value]
                elif variable in self.variables:
                    if len(value)!=1:
                        raise ValueError(f"For key {key} (variable {variable}), the values was {value}, but it's not iteration, so exactly one element in the list is expected")
                    element = value[0]
                    if element not in self.variables[variable].string_values_to_value:
                        raise ValueError(f"Value `{value}` for key {key} (variable {variable}) is not in the dictionary")
                    result[variable] = self.variables[variable].string_values_to_value[element]
                else:
                    raise ValueError(f"key {key} is neither variable not subdomain")
        return result


