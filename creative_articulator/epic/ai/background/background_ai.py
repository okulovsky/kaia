from ....common import Node
from ...model import NodeData
from .node_picker import find_node_to_process, BackgroundConfirmation
from foundation_kaia.misc import lock
from .background_processor import IBackgroundProcessor

class BackgroundAI:
    def __init__(self,
                 root: Node,
                 processors: list[IBackgroundProcessor]
                 ):
        self.root = root
        self.processors = processors

    def iteration(self) -> bool:
        with lock(self.root):
            node = find_node_to_process(self.root)
        if node is None:
            return False
        for processor in self.processors:
            with lock(self.root):
                task = processor.prepare(node)
            if task is None:
                continue
            result = processor.execute(task)
            with lock(self.root):
                processor.apply(node, task, result)
        with lock(self.root):
            node[BackgroundConfirmation] = BackgroundConfirmation(node[NodeData].simhash)
        return True




