from unittest import TestCase
from brainbox.framework import Job, BrainBoxTask, BrainBoxBase, BrainBoxService, Loc, Core, ControllerRegistry, IDecider, CheckReadyAction
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine

class A(IDecider):
    def __call__(self, a=1, b=2):
        return a+b


class CheckReadyActionTestCase(TestCase):

    def check(self, core: Core, statuses):
        with Session(core._engine) as session:
            result = list(session.execute(select(Job.id, Job.ready)))
            result = {int(r.id) : r.ready for r in result}
            self.assertEqual(statuses, tuple(result[i] for i in range(4)))


    def close(self, core: Core, id: str):
        with Session(core._engine) as session:
            core.close_job(session, core.get_job_by_id(session, id), '')
            session.commit()

    def test_readiness(self):
        with Loc.create_test_file() as file:
            engine = create_engine('sqlite:///'+str(file))
            BrainBoxBase.metadata.create_all(engine)

            with Session(engine) as session:
                job_0 = BrainBoxTask.call(A)().to_task(id='0')
                job_3 = BrainBoxTask.call(A)().to_task(id='3')
                job_2 = BrainBoxTask.call(A)(a=job_3).to_task(id='2')
                job_1 = BrainBoxTask.call(A)(a=job_2, b=job_0).to_task(id='1')


                jobs = BrainBoxTask.to_all_jobs([job_3, job_2, job_1, job_0])
                for job in jobs:
                    session.add(job.set_defaults())
                session.commit()

            core = Core(engine, ControllerRegistry([A()]))

            CheckReadyAction().apply(core)
            self.check(core, (True, False, False, True))

            self.close(core, '0')
            CheckReadyAction().apply(core)
            self.check(core, (True, False, False, True))

            self.close(core, '3')
            CheckReadyAction().apply(core)
            self.check(core, (True, False, True, True))

            self.close(core, '2')
            CheckReadyAction().apply(core)
            self.check(core, (True, True, True, True))

            engine.dispose()


