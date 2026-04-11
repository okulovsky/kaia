from unittest import TestCase
from brainbox.framework import Job, BrainBox, BrainBoxTask, BrainBoxBase, Core, ControllerRegistry, \
    ISelfManagingDecider, CheckReadyAction, BrainBoxLocations
from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine
from foundation_kaia.misc import Loc

class A(ISelfManagingDecider):
    def run(self, a=1, b=2):
        return a+b


class CheckReadyActionTestCase(TestCase):

    def check(self, core: Core, statuses):
        with Session(core._engine) as session:
            result = list(session.execute(select(Job.id, Job.ready_timestamp.is_not(None).label('ready'))))
            result = {int(r.id) : r.ready for r in result}
            self.assertEqual(statuses, tuple(result[i] for i in range(4)))


    def close(self, core: Core, id: str):
        with Session(core._engine) as session:
            core.close_job(session, core.get_job_by_id(session, id), '')
            session.commit()

    def test_readiness(self):
        with Loc.create_test_folder() as folder:
            locations = BrainBoxLocations.default(folder)

            engine = create_engine('sqlite:///'+str(locations.db_path))
            BrainBoxBase.metadata.create_all(engine)

            with Session(engine) as session:
                job_0 = BrainBox.TaskBuilder.call(A, id='0').run()
                job_3 = BrainBox.TaskBuilder.call(A, id='3').run()
                job_2 = BrainBox.TaskBuilder.call(A, id='2').run(a=job_3)
                job_1 = BrainBox.TaskBuilder.call(A, id='1').run(a=job_2, b=job_0)

                job_descs = BrainBoxTask.several_to_job_descriptions([job_3, job_2, job_1, job_0])
                for job in job_descs:
                    session.add(job.to_job())
                session.commit()

            core = Core(engine, ControllerRegistry([A()]), locations.cache_folder)

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


