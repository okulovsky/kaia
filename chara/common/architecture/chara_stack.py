import os
from pathlib import Path
from dataclasses import dataclass

from foundation_kaia.marshalling import FunctionKind
from foundation_kaia.marshalling.reflector import Signature


@dataclass
class CharaStackItem:
    folder: Path
    name: str | None
    index: int
    childen_count: int


class CharaStack:
    def __init__(self, root: Path):
        self.root = root
        self.exited = False
        self.stack: list[CharaStackItem] = []
        self.last_exited: CharaStackItem|None = None

    def check_exited(self):
        if self.exited:
            raise ValueError("Stack already exited")

    def push(self, name: str) -> CharaStackItem:
        self.check_exited()
        if len(self.stack) == 0:
            self.stack.append(CharaStackItem(
                self.root,
                None,
                0,
                0
            ))
        else:
            parent = self.stack[-1]
            new_index = parent.childen_count
            folder_name = str(new_index).zfill(3) + "-" + name
            parent.childen_count += 1
            self.stack.append(CharaStackItem(
                parent.folder / folder_name,
                name,
                new_index,
                0
            ))
            with open(parent.folder / '.cache', 'a') as f:
                f.write(folder_name + '\n')
        os.makedirs(self.stack[-1].folder, exist_ok=True)
        return self.stack[-1]

    def pop(self):
        self.check_exited()
        self.last_exited = self.stack.pop()
        if len(self.stack) == 0:
            self.exited = True





