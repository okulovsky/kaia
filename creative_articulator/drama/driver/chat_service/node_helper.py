import pickle
from dataclasses import dataclass
from ...data import Node, Message
from pathlib import Path

@dataclass
class TreeStatus:
    selected: bool = False
    is_root: bool = False

@dataclass
class MessageBranch:
    parent: Node
    target: Node
    descendants: list[Node]


class NodeHelper:
    def __init__(self, path_to_log_file: Path|None = None):
        self.path_to_log_file: Path = path_to_log_file
        self.current: Node = Node()
        self.current[TreeStatus] = TreeStatus(selected=True, is_root=True)

    def select(self, node: Node):
        node[TreeStatus].selected = True
        for n in node.siblings():
            n[TreeStatus].selected = False

    def get_selected_child(self, node: Node) -> Node | None:
        if len(node.children) == 0:
            return None

        for n in node.children:
            if n[TreeStatus].selected:
                return n

        raise ValueError("There are children in node, but none are selected")

    def find_message_in_current_branch(self, message_id: str) -> MessageBranch:
        result = MessageBranch(None, None, [])
        node = self.current
        while True:
            should_break = False
            msg = node.get(Message)
            if msg is not None and msg.id == message_id:
                result.target = node
                should_break = True
            else:
                result.descendants.append(node)
            node = node.parent
            if node is None:
                raise ValueError("Message not found")
            if should_break:
                break
        result.parent = node
        return result

    def find_node_by_message_id(self, message_id: str) -> Node | None:
        for node in self.current.root.descendants():
            msg = node.get(Message)
            if msg is not None and msg.id == message_id:
                return node
        return None

    def append_message(self, message: Message):
        node = Node()
        node[Message] = message
        self.current.append(node)
        self.select(node)
        self.current = node

    def save(self):
        if self.path_to_log_file is not None:
            self.path_to_log_file.write_bytes(pickle.dumps(self.current))

    def load(self):
        if self.path_to_log_file is not None and self.path_to_log_file.is_file():
            self.current = pickle.loads(self.path_to_log_file.read_bytes())
        else:
            self.current: Node = Node()
            self.current[TreeStatus] = TreeStatus(selected=True, is_root=True)
