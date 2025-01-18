import time
from sqlalchemy import Column, DateTime, func, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from unittest import TestCase
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, mapped_column, MappedColumn, declared_attr
from datetime import datetime

Base = declarative_base()


class Model(Base):
    __tablename__ = 'model'

    id: MappedColumn[int] = mapped_column(primary_key=True)
    name: MappedColumn[str] = mapped_column(nullable=False)
    last_updated: MappedColumn[datetime] = mapped_column(
        default=func.strftime('%Y-%m-%d %H:%M:%f', 'now'),
        onupdate=func.strftime('%Y-%m-%d %H:%M:%f', 'now')
    )

    def __repr__(self):
        return f'{self.id}/{self.name}/{self.last_updated}'


def load(engine) -> dict[int,Model]:
    with Session(engine) as session:
        result = list(session.query(Model))
    return {r.id:r for r in result}

class LastUpdatedTestCase(TestCase):
    def test_last_updated(self):
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            for i in range(3):
                session.add(Model(id=i, name=f'test-{i}'))
            session.commit()

        self.assertEqual(3, len(load(engine)))

        with Session(engine) as session:
            session.add(Model(id=3, name=f'test-3'))
            session.commit()

        r = load(engine)
        self.assertGreater(r[3].last_updated, r[2].last_updated)
        now = datetime.now()

        with Session(engine) as session:
            model = session.scalar(session.query(Model).where(Model.id==1))
            model.name = 'updated'
            session.commit()

        r = load(engine)

        self.assertGreater(r[1].last_updated, r[3].last_updated)

        timestamp = r[2].last_updated

        with Session(engine) as session:
            result = list(session.query(Model).where(Model.last_updated>timestamp))
            ids = set(r.id for r in result)
            self.assertSetEqual({1,3}, ids)

        engine.dispose()


