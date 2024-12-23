import unittest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event, select
from brainbox.framework.job_processing.core import TrackableSessionFactory


# Base class for declarative models
Base = declarative_base()

# Sample model class
class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


# Custom session factory that attaches event listeners
# Unit test class
class TestSQLAlchemyChangeTracking(unittest.TestCase):

    def setUp(self):
        # Set up an in-memory SQLite database and session
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.tracker = TrackableSessionFactory(self.engine, lambda job: job.name)

    def tearDown(self):
        # Drop all tables after each test
        Base.metadata.drop_all(self.engine)

    def test_change_tracking(self):
        with self.tracker() as session:
            # Add a new Job
            job1 = Job(name="Job1")
            session.add(job1)
            session.commit()

        self.assertEqual(["Job1"], self.tracker.changes.added)
        self.assertEqual([], self.tracker.changes.modified)
        self.assertEqual([], self.tracker.changes.deleted)

        with self.tracker() as session:
            job1_1 = session.scalar(select(Job).where(Job.name=='Job1'))
            job1_1.name = "Job1_1"
            session.commit()

        self.assertEqual(['Job1'], self.tracker.changes.added)
        self.assertEqual(['Job1_1'], self.tracker.changes.modified)
        self.assertEqual([], self.tracker.changes.deleted)

        with self.tracker() as session:
            job1_2 = session.scalar(select(Job).where(Job.name == "Job1_1"))
            session.delete(job1_2)
            session.commit()
        # Verify modified entities

        self.assertEqual(['Job1'], self.tracker.changes.added)
        self.assertEqual(['Job1_1'], self.tracker.changes.modified)
        self.assertEqual(['Job1_1'], self.tracker.changes.deleted)


        session.close()

    def method(self):
        with self.tracker() as session:
            # Add a new Job
            job1 = Job(name="Job1")
            session.add(job1)
            session.commit()
    def test_with_different_methods(self):
        self.method()
        print(self.tracker.changes.added[0])

