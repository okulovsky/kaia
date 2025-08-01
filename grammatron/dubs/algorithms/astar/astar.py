from dataclasses import dataclass, field
from typing import List
import heapq
import networkx as nx
from typing import Generator
from .graph_builder import EPSILON_TRANSITION_LABEL



@dataclass
class SearchState:
    node: str                          # current node in graph
    input_position: int               # index in input string S
    collected_output: List[str]       # output sequence we're building
    collected_penalty: int            # total edit penalty so far
    input_length: int                 # total input length for heuristic
    priority: int = field(init=False) # f = g + h

    def __post_init__(self):
        self.priority = compute_priority(self)

    def __lt__(self, other: "SearchState") -> bool:
        return self.priority < other.priority


def compute_priority(state: SearchState) -> int:
    return state.collected_penalty


def astar_levenshtein(G: nx.DiGraph, S: str) -> Generator[SearchState, None, None]:
    start_node = G.graph["start"]
    accepting_nodes = G.graph["accepting"]
    input_length = len(S)

    # Initialize heap with start state
    heap: list[SearchState] = [
        SearchState(
            node=start_node,
            input_position=0,
            collected_output=[],
            collected_penalty=0,
            input_length=input_length
        )
    ]

    visited = set()

    while heap:
        state = heapq.heappop(heap)
        key = (state.node, state.input_position)

        if key in visited:
            continue
        visited.add(key)

        if state.node in accepting_nodes and state.input_position == input_length:
            yield state
            # Don't return — keep exploring better matches

        for _, next_node, data in G.out_edges(state.node, data=True):
            label = data["label"]

            if label == EPSILON_TRANSITION_LABEL:
                # ε-transition: skip ahead in graph without consuming input or penalty
                heapq.heappush(heap, SearchState(
                    node=next_node,
                    input_position=state.input_position,
                    collected_output=state.collected_output.copy(),
                    collected_penalty=state.collected_penalty,
                    input_length=input_length
                ))
                continue

            # Match or substitute
            if state.input_position < input_length:
                current_char = S[state.input_position]

                if label == current_char:
                    # Match: no penalty
                    heapq.heappush(heap, SearchState(
                        node=next_node,
                        input_position=state.input_position + 1,
                        collected_output=state.collected_output + [label],
                        collected_penalty=state.collected_penalty,
                        input_length=input_length
                    ))

                # Substitution
                heapq.heappush(heap, SearchState(
                    node=next_node,
                    input_position=state.input_position + 1,
                    collected_output=state.collected_output + [label],
                    collected_penalty=state.collected_penalty + 1,
                    input_length=input_length
                ))

            # Insertion: advance in graph without consuming input
            heapq.heappush(heap, SearchState(
                node=next_node,
                input_position=state.input_position,
                collected_output=state.collected_output + [label],
                collected_penalty=state.collected_penalty + 1,
                input_length=input_length
            ))

        # Deletion: skip a character in the input without consuming a graph edge
        if state.input_position < input_length:
            heapq.heappush(heap, SearchState(
                node=state.node, #This won't work anyway because r.n. it doesn't re-enter the node
                input_position=state.input_position + 1, #This is wrongly not inside IF
                collected_output=state.collected_output.copy(),
                collected_penalty=state.collected_penalty + 1,
                input_length=input_length
            ))