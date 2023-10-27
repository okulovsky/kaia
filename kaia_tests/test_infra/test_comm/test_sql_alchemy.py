from typing import *
from unittest import TestCase

from sqlalchemy.orm import declarative_base, Mapped, mapped_column, Session
from sqlalchemy import select, JSON


from kaia.infra.comm import Sql
from kaia.infra import Loc
from datetime import datetime

Base = declarative_base()

class Record(Base):
    __tablename__ = "records"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=True)
    timestamp: Mapped[datetime] = mapped_column(nullable=True)
    json: Mapped[List[str]] = mapped_column(type_=JSON)

    def __repr__(self):
        return f"Record(id = {self.id}, name = {self.name}, timestamp = {self.timestamp})"

class SqlAlchemyTestCase(TestCase):
    def test_sql_alchemy(self):
        sql = Sql.test_file('sqlalchemy')
        engine = sql.engine()
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            records = [Record(id=i, name = f'name_{i}', timestamp=datetime(2020+i,i+1, i+1), json=[j for j in range(i)]) for i in range(5)]
            session.add_all(records)
            session.commit()

        records = sql.perform(lambda cursor: list(cursor.execute(f'select * from records')))
        self.assertEqual(5, len(records))

        with Session(engine) as session:
            query = select(Record).where(Record.name>='name_3')
            results = list(session.scalars(query))
            self.assertEqual(2, len(results))
            self.assertEqual(3, len(results[0].json))
            for result in results:
                result.timestamp = None
            session.commit()

        records = sql.perform(lambda cursor: list(cursor.execute(f'select * from records')))
        self.assertIsNone(records[3][2])
        self.assertIsNone(records[4][2])

        with Session(engine) as session:
            for row in session.scalars(select(Record)):
                print(row.__dict__)






