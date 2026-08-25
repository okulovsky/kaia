from dataclasses import dataclass


@dataclass
class Separation:
    # Ordered ids of the child nodes this node was split into: sections for a
    # file, blocks for a section. Each id is a random guid assigned when the
    # child is first created - it carries no relation to content. If the text
    # is later edited insignificantly, collate() keeps this same id so the
    # node (and its downstream stats) survives the edit.
    ids: list[str]
