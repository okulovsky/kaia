from typing import *
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, Session
from sqlalchemy import create_engine, func, JSON, Column, select
from datetime import datetime


Base = declarative_base()

class BusItem(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column()
    type: Mapped[str] = mapped_column()
    payload = Column('payload', JSON)

    def __str__(self):
        return f'BusItem(id={self.id}, session_id="{self.session_id}", type="{self.type}", payload="{self.payload}")'

    def __repr__(self):
        return self.__str__()

class Bus:
    def __init__(self, db_path):
        self.db_path = db_path
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine('sqlite:///' + str(self.db_path))
            Base.metadata.create_all(self.engine)
        return self._engine

    def add_message(self, item: BusItem) -> int:
        with Session(self.engine) as session:
            session.add(item)
            session.commit()
            return item.id


    def get_messages(self, session_id: str|None, last_message_id: int|None):
        with Session(self.engine) as session:
            query = session.query(BusItem)
            if session_id is not None:
                query = query.where(BusItem.session_id == session_id)
            if last_message_id is not None:
                query = query.where(BusItem.id>last_message_id)
            return query.all()

    def get_sessions(self):
        with Session(self.engine) as session:
            return [c[0] for c in session.query(func.distinct(BusItem.session_id))]

    def get_max_message_id(self, session_id: str):
        with Session(self.engine) as session:
            query = select(func.max(BusItem.id)).where(BusItem.session_id == session_id)
            return session.execute(query).scalar()
