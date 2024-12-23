from unittest import TestCase
from brainbox.framework import Job, BrainBoxTask, BrainBoxBase, BrainBoxService, Loc, Core, ControllerRegistry, IDecider, RemoveIncorrectJobsAction
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine

class A(IDecider):
    def __call__(self, a=1, b=2):
        return a+b

class B(IDecider):
    def __call__(self, a=1, b=2):
        return a-b


class InternalFunctionsTest(TestCase):
    def test_remove_incorrect_tasks(self):
        with Loc.create_test_file() as file:
            engine = create_engine('sqlite:///'+str(file))
            BrainBoxBase.metadata.create_all(engine)

            with Session(engine) as session:
                jobs = [
                    BrainBoxTask.call(A)().to_task(id='1'),
                    BrainBoxTask.call(A)().to_task(id='2'),
                    BrainBoxTask.call(B)().to_task(id='3'),

                ]
                for job in BrainBoxTask.to_all_jobs(jobs):
                    session.add(job.set_defaults())
                session.commit()

            core = Core(engine, ControllerRegistry([A()]))

            RemoveIncorrectJobsAction().apply(core)

            with Session(engine) as session:
                result = list(session.execute(select(Job.id, Job.finished)))

            engine.dispose()

        result = {z[0]:z[1] for z in result}
        self.assertDictEqual({'1': False, '2': False, '3': True}, result)
