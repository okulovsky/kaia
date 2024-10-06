from typing import *
from .automaton import Automaton, ContextRequest, AutomatonExit
from dataclasses import dataclass

@dataclass
class TranslatorInputPackage:
    outer_context: Any
    inner_context: Any
    outer_input: Any

@dataclass
class TranslatorOutputPackage:
    outer_context: Any
    inner_context: Any
    inner_output: Any


class Translator:
    InputPackage = TranslatorInputPackage
    OutputPackage = TranslatorOutputPackage
    NoInput = object()
    def __init__(self,
                 inner_function,
                 context_translator: Optional[Callable] = None,
                 input_function_translator: Optional[Callable[[TranslatorInputPackage], Any]] = None,
                 input_generator_translator: Optional[Callable[[TranslatorInputPackage], Generator]] = None,
                 output_function_translator: Optional[Callable[[TranslatorOutputPackage], Any]] = None,
                 output_generator_translator: Optional[Callable[[TranslatorOutputPackage], Generator]] = None,
                 ):
        self.inner_function = inner_function
        self.context_translator = context_translator
        self.input_function_translator = input_function_translator
        self.input_generator_translator = input_generator_translator
        self.output_function_translator = output_function_translator
        self.output_generator_translator = output_generator_translator
        if self.input_generator_translator is not None and self.input_function_translator is not None:
            raise ValueError(f"Both input function translator and input generator translator cannot be set")
        if self.output_function_translator is not None and self.output_generator_translator is not None:
            raise ValueError(f"Both output function translator and output generator translator cannot be set")


    def __call__(self):
        outer_context = yield ContextRequest()
        if self.context_translator is not None:
            inner_context = self.context_translator(outer_context)
        else:
            inner_context = outer_context
        automaton = Automaton(self.inner_function, inner_context)
        outer_input = yield
        while True:
            input_pack = TranslatorInputPackage(outer_context, inner_context, outer_input)
            if self.input_function_translator is not None:
                inner_input = self.input_function_translator(input_pack)
            elif self.input_generator_translator is not None:
                inner_input = yield from self.input_generator_translator(input_pack)
            else:
                inner_input = outer_input

            if inner_input is Translator.NoInput:
                continue

            inner_output = automaton.process_and_rethrow_exit(inner_input)
            
            output_pack = TranslatorOutputPackage(outer_context, inner_context, inner_output)
            if self.output_function_translator is not None:
                outer_input = yield self.output_function_translator(output_pack)

            elif self.output_generator_translator is not None:
                yield from self.output_generator_translator(output_pack)
                outer_input = yield None
            else:
                outer_input = yield inner_output

    @staticmethod
    def translate(routine: Callable) -> 'TranslatorBuilder':
        return TranslatorBuilder(routine)


class TranslatorBuilder:
    def __init__(self, inner_routine):
        self.inner_routine = inner_routine

    def translator(self, translator_factory: Callable[[Any], Translator]) -> 'TranslatorBuilder':
        return TranslatorBuilder(translator_factory(self.inner_routine))

    def context(self, context_translator: Callable[[Any], Any]) -> 'TranslatorBuilder':
        return TranslatorBuilder(Translator(self.inner_routine, context_translator=context_translator))

    def input_function(self, input_function: Callable[[Any], Any]) -> 'TranslatorBuilder':
        return TranslatorBuilder(Translator(self.inner_routine, input_function_translator=input_function))

    def input_generator(self, input_generator: Callable[[Any], Generator]) -> 'TranslatorBuilder':
        return TranslatorBuilder(Translator(self.inner_routine, input_generator_translator=input_generator))

    def output_function(self, output_function: Callable[[Any], Any]) -> 'TranslatorBuilder':
        return TranslatorBuilder(Translator(self.inner_routine, output_function_translator=output_function))

    def output_generator(self, output_generator: Callable[[Any], Generator]) -> 'TranslatorBuilder':
        return TranslatorBuilder(Translator(self.inner_routine, output_generator_translator=output_generator))

    def __call__(self):
        return self.inner_routine()
