from unittest import TestCase
from brainbox.framework import Job, BrainBox, BrainBoxTask, BrainBoxBase, ISelfManagingDecider, Core, \
    ControllerRegistry, IDecider, RemoveIncorrectJobsAction, BrainBoxLocations
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine
from foundation_kaia.misc import Loc

class A(ISelfManagingDecider):
    def run(self, a=1, b=2):
        return a+b

class B(ISelfManagingDecider):
    def run(self, a=1, b=2):
        return a-b


class InternalFunctionsTest(TestCase):
    def test_remove_incorrect_tasks(self):
        with Loc.create_test_folder() as folder:
            locations = BrainBoxLocations.default(folder)

            engine = create_engine('sqlite:///'+str(locations.db_path))
            BrainBoxBase.metadata.create_all(engine)

            with Session(engine) as session:
                tasks = [
                    BrainBox.TaskBuilder.call(A, id='1').run(),
                    BrainBox.TaskBuilder.call(A, id='2').run(),
                    BrainBox.TaskBuilder.call(B, id='3').run(),
                ]
                for job in BrainBoxTask.several_to_job_descriptions(tasks):
                    session.add(job.to_job())
                session.commit()

            core = Core(engine, ControllerRegistry([A()]), locations.cache_folder)

            RemoveIncorrectJobsAction().apply(core)

            with Session(engine) as session:
                result = list(session.execute(select(Job.id, Job.finished_timestamp.is_not(None).label('finished'))))

            engine.dispose()

        result = {z[0]:z[1] for z in result}
        self.assertDictEqual({'1': False, '2': False, '3': True}, result)
