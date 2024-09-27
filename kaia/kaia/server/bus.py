from typing import *
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, Session
from sqlalchemy import create_engine, func, JSON, Column
from datetime import datetime


Base = declarative_base()

class BusItem(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column()
    timestamp: Mapped[datetime] = mapped_column()
    type: Mapped[str] = mapped_column()
    payload = Column('payload', JSON)


class Bus:
    def __init__(self, db_path):
        self.engine = create_engine('sqlite:///' + str(db_path))
        Base.metadata.create_all(self.engine)

    def add_message(self, item: BusItem):
        with Session(self.engine) as session:
            session.add(item)
            session.commit()


    def get_messages(self, session_id: str, last_message_id: int|None):
        with Session(self.engine) as session:
            query = session.query(BusItem).where(BusItem.session_id==session_id)
            if last_message_id is not None:
                query = query.where(BusItem.id>last_message_id)
            return query.all()

    def get_sessions(self):
        with Session(self.engine) as session:
            return [c[0] for c in session.query(func.distinct(BusItem.session_id))]


