from unittest import TestCase
from brainbox.framework import Job, BrainBoxBase, Loc
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import datetime


class DBTestCase(TestCase):
    def test_db(self):
        with Loc.create_test_file('brainbox-database') as path:
            engine = create_engine("sqlite:///"+str(path))
            BrainBoxBase.metadata.create_all(engine)
            with Session(engine) as session:
                jobs = list(session.scalars(select(Job)))
                self.assertEqual(0, len(jobs))
            with Session(engine) as session:
                session.add(Job(id='test', decider='test', arguments=dict(a=1), batch='batch', has_dependencies=False, received_timestamp=datetime.now()))
                session.commit()
            with Session(engine) as session:
                jobs = list(session.scalars(select(Job)))
                self.assertEqual(1, len(jobs))



