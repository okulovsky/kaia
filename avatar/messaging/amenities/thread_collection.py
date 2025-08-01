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
    confirmed_parents: list['ThreadMessage'] = field(default_factory=list)

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

    def make_confirmation_consistancy(self):
        if self.message.envelop.confirmation_for is not None:
            pnode = self
            while True:
                pnode = pnode.parent
                if pnode is None:
                    break
                if self.message.is_confirmation_of(pnode.message):
                    self.confirmed_parents.append(pnode)
                    break
        for snode in self.children:
            snode.make_confirmation_consistancy()

    def iterate_nodes(self):
        yield self
        for node in self.children:
            yield from node.iterate_nodes()


@dataclass
class ThreadRoot:
    starting_message: 'ThreadMessage'
    last_update: datetime = datetime(1000,1,1)
    first_update: datetime|None = datetime(3000,1,1)

    @property
    def starting_message_id(self) -> str:
        return self.starting_message.message.envelop.id

    def print(self):
        for node in self.starting_message.iterate_nodes():
            levels = ['  ']*(node.level)
            for cparent in node.confirmed_parents:
                levels[cparent.level] = 'X '
            time = int((node.message.envelop.timestamp - self.first_update).total_seconds())
            print(''.join(levels)+f'{type(node.message).__name__} (+{time}s)')



class ThreadCollection:
    def __init__(self):
        self.id_to_thread: defaultdict[str, ThreadRoot] = defaultdict(ThreadRoot)
        self.id_to_message: defaultdict[str, ThreadMessage] = defaultdict(ThreadMessage)

    def pull_changes(self, changes: Iterable[IMessage]):
        changed_threads = set()
        for message in changes:
            self.id_to_message[message.envelop.id].message = message
            if message.envelop.reply_to is None:
                new_thread = ThreadRoot(ThreadMessage(message))
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
            thread.starting_message.make_confirmation_consistancy()

    def get_top_topics(self, count: int|None = None) -> list[ThreadRoot]:
        query = Query.dict(self.id_to_thread).order_by_descending(lambda z: z.value.last_update)
        if count is not None:
            query = query.take(count)
        return query.select(lambda z: z.value).to_list()

    Root = ThreadRoot
    Message = ThreadMessage




