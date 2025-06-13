from dataclasses import dataclass
from ...core import IDub, DubParameters
from ..regex.regex_parser import RegexParser, RegexParserData
from .graph_builder import GraphBuilder
from .astar import astar_levenshtein
import networkx as nx
import random
import string

@dataclass
class AStarParserData:
    graph: nx.DiGraph
    parser: RegexParser


def astar_parser_data(dub: IDub, parameters: DubParameters):
    parser = RegexParser(dub, parameters)
    graph = nx.DiGraph()
    builder = GraphBuilder(parser.data.parser_data.root, graph, parser.data.parser_data.variables).build()
    graph.graph["start"] = builder.start_node
    graph.graph["accepting"] = builder.end_node
    return AStarParserData(graph, parser)


class AStarParser:
    def __init__(self, dub: IDub, parameters: DubParameters|None = None):
        self.data: AStarParserData = dub.get_cached_value(astar_parser_data, parameters)

    def nearest_string(self, s):
        best_candidate = None
        best_value = None
        for state in astar_levenshtein(self.data.graph, s):
            if best_value is None or state.collected_penalty < best_value:
                best_value = state.collected_penalty
                best_candidate = ''.join(state.collected_output)
                break
        return best_candidate

    def parse(self, s: str):
        return self.data.parser.parse(self.nearest_string(s))

    @staticmethod
    def add_noise_to_string(text: str, deletions: int = 0, insertions: int = 0, changes: int = 0) -> str:
        text = list(text)

        # Apply deletions
        for _ in range(deletions):
            if text:
                idx = random.randrange(len(text))
                del text[idx]

        # Apply changes (substitutions)
        for _ in range(changes):
            if text:
                idx = random.randrange(len(text))
                text[idx] = random.choice(string.ascii_letters + string.digits + string.punctuation + ' ')

        # Apply insertions
        for _ in range(insertions):
            idx = random.randrange(len(text) + 1)
            char = random.choice(string.ascii_letters + string.digits + string.punctuation + ' ')
            text.insert(idx, char)

        return ''.join(text)




