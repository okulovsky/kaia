from typing import Tuple, Optional, Iterable
from dataclasses import dataclass, field
from ..stream import IMessage
from datetime import datetime
from collections import defaultdict
from yo_fluq import Query


@dataclass
class ThreadMessage:
    message: IMessage|None = None
    children: list['ThreadMessage'] = field(default_factory=list)
    level: int = 0
    parent: Optional['ThreadMessage'] = None
    root: Optional['ThreadRoot'] = None

    def make_parent_consistancy(self, root: 'ThreadRoot', parent: Optional['ThreadMessage']):
        self.parent = parent
        self.root = root
        if parent is not None:
            self.level = parent.level + 1
        else:
            self.level = 0
        root.last_update = max(root.last_update, self.message.envelop.timestamp)
        root.first_update = min(root.first_update, self.message.envelop.timestamp)
        for child in self.children:
            child.make_parent_consistancy(root, self)

    def iterate_nodes(self):
        yield self
        for node in self.children:
            yield from node.iterate_nodes()

    def iterate_parents(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent


@dataclass
class ReportLineLevel:
    is_confirmation: bool = False
    is_continuation: bool = False


@dataclass
class ReportLine:
    message: IMessage
    levels: tuple[ReportLineLevel,...]
    time: float

@dataclass
class ThreadRoot:
    starting_message: 'ThreadMessage'
    last_update: datetime = datetime(1000,1,1)
    first_update: datetime|None = datetime(3000,1,1)

    @property
    def starting_message_id(self) -> str:
        return self.starting_message.message.envelop.id

    def to_report(self) -> list[ReportLine]:
        result = []
        for node in self.starting_message.iterate_nodes():
            levels = [ReportLineLevel() for _ in range(node.level)]
            for parent_idx, parent in enumerate(node.iterate_parents()):
                level = levels[-(parent_idx+1)]
                if (node.message.envelop.confirmation_stack is not None
                        and  parent.message.envelop.id in node.message.envelop.confirmation_stack):
                    level.is_continuation = True
                if node.message.is_confirmation_of(parent.message):
                    level.is_confirmation = True
            time = int((node.message.envelop.timestamp - self.first_update).total_seconds())
            result.append(ReportLine(
                node.message,
                tuple(levels),
                time
            ))
        return result

    def to_str(self):
        for line in self.to_report():
            prefix = ''
            for level in line.levels:
                prefix+= 'X' if level.is_confirmation else ' '
                prefix+= '*' if level.is_continuation else ' '
                prefix+= '  '
            yield f'{prefix}{type(line.message).__name__} ({line.time}s)'

    def print(self):
        for line in self.to_str():
            print(line)








class ThreadCollection:
    def __init__(self):
        self.id_to_thread: defaultdict[str, ThreadRoot] = defaultdict(ThreadRoot)
        self.id_to_message: defaultdict[str, ThreadMessage] = defaultdict(ThreadMessage)

    def pull_changes(self, changes: Iterable[IMessage]):
        changed_threads = set()
        for message in changes:
            self.id_to_message[message.envelop.id].message = message
            if message.envelop.reply_to is None:
                new_thread = ThreadRoot(self.id_to_message[message.envelop.id])
                self.id_to_thread[new_thread.starting_message_id] = new_thread
                changed_threads.add(new_thread.starting_message_id)
            else:
                parent_message = self.id_to_message[message.envelop.reply_to]
                parent_message.children.append(self.id_to_message[message.envelop.id])
                if parent_message.root is not None: #otherwise, the parent message added the thread_id in the collection
                    changed_threads.add(parent_message.root.starting_message_id)

        for thread_id in changed_threads:
            thread = self.id_to_thread[thread_id]
            thread.starting_message.make_parent_consistancy(thread, None)


    def get_top_topics(self, count: int|None = None) -> list[ThreadRoot]:
        query = Query.dict(self.id_to_thread).order_by_descending(lambda z: z.value.last_update)
        if count is not None:
            query = query.take(count)
        return query.select(lambda z: z.value).to_list()

    Root = ThreadRoot
    Message = ThreadMessage


    @staticmethod
    def just_print(messages: Iterable[IMessage], return_str: bool = False):
        collection = ThreadCollection()
        collection.pull_changes(messages)
        result = []
        method = result.append if return_str else print
        for thread in collection.get_top_topics():
            for line in thread.to_str():
                method(line)
            method('\n\n')
        if return_str:
            return '\n'.join(result)



