from typing import Iterable
from ...rules import Rule
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

class Node:
    def __init__(self, caption: str|None = None, group: str|None = None):
        self.caption = caption
        self.group = group

class RuleNode(Node):
    def __init__(self, rule: Rule):
        if '/' in rule.name:
            group, caption = rule.name.split("/", 1)
            super().__init__(caption, group)
        else:
            super().__init__(rule.name)

        self.publisher = rule.name
        self.output_edge_count = {} if rule.outputs is None else {output:0 for output in rule.outputs}
        self.input_edge_count = 0
        self.connector = rule.input


class EdgeType(Enum):
    output = 0
    call = 1
    external = 2

@dataclass
class Edge:
    edge_type: EdgeType
    from_node: Node
    to_node: Node
    message_type: type|None = None

class GraphBuilder:
    def __init__(self, rules: Iterable[Rule]):
        self.rules = list(rules)
        self.rule_nodes: list[RuleNode] = []
        self.external_sources: dict[type, Node] = defaultdict(Node)
        self.external_destinations: dict[type, Node] = defaultdict(Node)
        self.sync_calls: list[Node] = []
        self.edges: list[Edge] = []


    def _generate_edges(self, from_node: RuleNode, to_node: RuleNode):
        for message_type in from_node.output_edge_count:
            if to_node.connector.check_incoming_internal(message_type, from_node.publisher):
                from_node.output_edge_count[message_type] += 1
                to_node.input_edge_count += 1
                self.edges.append(Edge(
                    EdgeType.output,
                    from_node,
                    to_node,
                    message_type
                ))


    def build(self):
        for rule in self.rules:
            rule_node = RuleNode(rule)
            self.rule_nodes.append(rule_node)
            for call in rule.calls:
                node = Node(call.argument_type.__name__+'/'+call.returned_type.__name__)
                self.sync_calls.append(node)
                self.edges.append(Edge(EdgeType.call, rule_node, node, None))

        for src in self.rule_nodes:
            for dst in self.rule_nodes:
                self._generate_edges(src, dst)

        for node in self.rule_nodes:
            if node.connector.type is not None:
                if node.input_edge_count == 0:
                    self.edges.append(Edge(
                        EdgeType.external,
                        self.external_sources[node.connector.type],
                        node,
                        node.connector.type
                    ))

            for message_type, count in node.output_edge_count.items():
                if count == 0:
                    self.edges.append(Edge(
                        EdgeType.external,
                        node,
                        self.external_destinations[message_type],
                        message_type
                    ))

