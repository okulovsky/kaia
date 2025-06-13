import uuid

import networkx as nx
from ...core.parser_intructions import *
from dataclasses import dataclass


EPSILON_TRANSITION_LABEL = 'epsilon-transition'

@dataclass
class GraphBuilder:
    instruction: IParserInstruction
    graph: nx.DiGraph
    variables: dict[tuple[str,...], VariableInfo]

    start_node: str|None = None
    end_node: str|None = None

    def build(self) -> 'GraphBuilder':
        for method in [self.on_constant, self.on_variable, self.on_sequence, self.on_union, self.on_subdomain, self.on_iteration]:
            result = method()
            if result is None:
                continue
            else:
                self.start_node, self.end_node = result
                break
        return self

    def next(self, element: IParserInstruction):
        return GraphBuilder(
            element,
            self.graph,
            self.variables
        )

    def new_node(self):
        return str(uuid.uuid4())

    def add_word_chain(self, word, start):
        prev = start
        for c in word:
            next = self.new_node()
            self.graph.add_edge(prev, next, label=c)
            prev = next
        return prev


    def on_constant(self):
        if isinstance(self.instruction, ConstantParserInstruction):
            start = self.new_node()
            return start, self.add_word_chain(self.instruction.value, start)

    def normalize(self, start, ends):
        if len(ends) == 0:
            return start, start
        if len(ends) == 1:
            return start, ends[0]
        end = self.new_node()
        for e in ends:
            self.graph.add_edge(e, end, label = EPSILON_TRANSITION_LABEL)
        return start, end

    def on_variable(self):
        if isinstance(self.instruction, VariableParserInstruction):
            start = self.new_node()
            ends = []
            for value in self.variables[self.instruction.variable_name].string_values_to_value:
                ends.append(self.add_word_chain(value, start))
            return self.normalize(start, ends)

    def on_sequence(self):
        if isinstance(self.instruction, SequenceParserInstruction):
            start = end = self.new_node()
            for element in self.instruction.sequence:
                g = self.next(element).build()
                self.graph.add_edge(end, g.start_node, label=EPSILON_TRANSITION_LABEL)
                end = g.end_node
            return start, end

    def on_union(self):
        if isinstance(self.instruction, UnionParserInstruction):
            start = self.new_node()
            exits = []
            for element in self.instruction.union:
                g = self.next(element).build()
                self.graph.add_edge(start, g.start_node, label=EPSILON_TRANSITION_LABEL)
                exits.append(g.end_node)
            return self.normalize(start, exits)

    def on_subdomain(self):
        if isinstance(self.instruction, SubdomainInstruction):
            g = GraphBuilder(self.instruction.subdomain.root, self.graph, self.instruction.subdomain.variables).build()
            return g.start_node, g.end_node

    def on_iteration(self):
        if isinstance(self.instruction, IterationParserInstruction):
            g = self.next(self.instruction.iterated).build()
            start = self.new_node()
            self.graph.add_edge(start, g.start_node, label = EPSILON_TRANSITION_LABEL)
            self.graph.add_edge(g.end_node, start, label = EPSILON_TRANSITION_LABEL)
            return start, start




