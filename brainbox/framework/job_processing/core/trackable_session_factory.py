from typing import Callable
from sqlalchemy.orm import Session
from sqlalchemy import event
from dataclasses import dataclass, field

class TrackableSessionFactory:
    @dataclass
    class Changes:
        modified: list = field(default_factory=list)
        added: list = field(default_factory=list)
        deleted: list = field(default_factory=list)

        @property
        def all(self) -> list:
            return self.modified+self.added+self.deleted

    def __init__(self, engine, selector:Callable):
        self.engine = engine
        self.selector = selector
        self.changes = TrackableSessionFactory.Changes()

    def __call__(self) -> Session:
        session = Session(self.engine)
        event.listen(session, 'before_commit', self._track_changes)
        return session

    def _track_changes(self, session):
        self.changes.modified.extend(self.selector(obj) for obj in session.dirty if session.is_modified(obj, include_collections=False))
        self.changes.added.extend(self.selector(obj) for obj in session.new)
        self.changes.deleted.extend(self.selector(obj) for obj in session.deleted)

    def reset(self):
        self.changes = TrackableSessionFactory.Changes()