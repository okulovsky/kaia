from typing import Any
from collections import defaultdict
from .graph_builder import GraphBuilder, Node, RuleNode, EdgeType

def render_rules_graph(builder: GraphBuilder, rankdir: str = "LR") -> Any:
    from graphviz import Digraph

    g = Digraph("RulesGraph", graph_attr={"rankdir": rankdir})

    # --- group rule nodes by .group ---
    grouped: dict[str, list[RuleNode]] = defaultdict(list)
    ungrouped: list[RuleNode] = []
    for node in builder.rule_nodes:
        if node.group:
            grouped[node.group].append(node)
        else:
            ungrouped.append(node)

    # --- grouped rule nodes in cluster_* subgraphs ---
    cluster_idx = 0
    for label, nodes in grouped.items():
        with g.subgraph(name=f"cluster_{cluster_idx}") as sg:
            sg.attr(
                label=label,
                color="#999999",
                style="rounded",
                penwidth="1.5",
                fontsize="12",
                fontname="Helvetica",
            )
            for node in nodes:
                sg.node(
                    _node_id(node),
                    label=node.caption or "",
                    shape="box",
                    fontsize="12",
                )
        cluster_idx += 1

    # --- ungrouped rule nodes at top level ---
    for node in ungrouped:
        g.node(
            _node_id(node),
            label=node.caption or "",
            shape="box",
            fontsize="12",
        )

    # --- external sources/destinations ---
    for ext_node in builder.external_sources.values():
        g.node(
            _node_id(ext_node),
            label="",
            shape="circle",
            width="0.2",
            height="0.2",
            fixedsize="true",
            style="filled",
            fillcolor="black",
        )
    for ext_node in builder.external_destinations.values():
        g.node(
            _node_id(ext_node),
            label="",
            shape="circle",
            width="0.2",
            height="0.2",
            fixedsize="true",
            style="filled",
            fillcolor="gray",
        )

    # --- sync_calls (dark, rounded) ---
    for call_node in builder.sync_calls:
        g.node(
            _node_id(call_node),
            label=call_node.caption or "",
            shape="ellipse",
            style="filled",
            fillcolor="#444444",
            fontcolor="white",
            fontsize="12",
        )

    # --- edges ---
    for edge in builder.edges:
        if edge.edge_type == EdgeType.output:
            style, color, dir_attr = "solid", "black", "forward"
        elif edge.edge_type == EdgeType.call:
            style, color, dir_attr = "solid", "black", "both"   # bidirectional
        else:  # EdgeType.external
            style, color, dir_attr = "dotted", "gray", "forward"

        g.edge(
            _node_id(edge.from_node),
            _node_id(edge.to_node),
            label=("" if edge.edge_type == EdgeType.call else edge.message_type.__name__),
            style=style,
            color=color,
            fontsize="10",
            fontname="Helvetica",
            arrowhead="normal",
            dir=dir_attr,
        )

    return g

def _node_id(node: Node) -> str:
    # Always unique/stable per object within the process
    return f"node_{id(node)}"
