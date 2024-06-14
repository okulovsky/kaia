from unittest import TestCase
from kaia.infra import Sql, Loc
from kaia.brainbox.core.small_classes import BrainBoxBase, BrainBoxJob, BrainBoxTask
from kaia.brainbox.core.api import BrainBoxService
from sqlalchemy.orm import Session, Bundle
from sqlalchemy import select



class InternalFunctionsTest(TestCase):

    def get_readiness(self, session):
        result = list(session.execute(select(BrainBoxJob.id, BrainBoxJob.ready)))
        result = {int(r.id) : r.ready for r in result}
        return tuple(result[i] for i in range(4))



    def test_readiness(self):
        with Loc.create_temp_file('tests/readiness', 'db') as file:
            engine = Sql.file(file).engine()
            BrainBoxBase.metadata.create_all(engine)
            with Session(engine) as session:
                session.add(BrainBoxJob.from_task(BrainBoxTask(id='0', decider='A', arguments={}, dependencies={'a':'1'})))
                session.add(BrainBoxJob.from_task(BrainBoxTask(id='1', decider='A', arguments={})))
                session.add(BrainBoxJob.from_task(BrainBoxTask(id='2', decider='A', arguments={}, dependencies={'a':'3', 'b': '1'})))
                session.add(BrainBoxJob.from_task(BrainBoxTask(id='3', decider='A', arguments={})))
                session.commit()
            service = BrainBoxService({'A': None}, None, None, None)
            service.engine = engine

            service.assign_ready()
            with Session(engine) as session:
                readiness = self.get_readiness(session)
                self.assertEqual((False, True, False, True), readiness)

            with Session(engine) as session:
                task = service.get_task_by_id(session, '1')
                service.close_task(task)
                session.commit()

            service.assign_ready()
            with Session(engine) as session:
                readiness = self.get_readiness(session)
                self.assertEqual((True, True, False, True), readiness)

            with Session(engine) as session:
                task = service.get_task_by_id(session, '3')
                service.close_task(task)
                session.commit()

            service.assign_ready()
            with Session(engine) as session:
                readiness = self.get_readiness(session)
                self.assertEqual((True, True, True, True), readiness)

            engine.dispose()





    def test_remove_incorrect_tasks(self):
        with Loc.create_temp_file('tests/remove_incorrect_tasks', 'db') as file:
            engine = Sql.file(file).engine()
            BrainBoxBase.metadata.create_all(engine)
            with Session(engine) as session:
                session.add(BrainBoxJob.from_task(BrainBoxTask(id='1', decider='A', arguments={})))
                session.add(BrainBoxJob.from_task(BrainBoxTask(id='2', decider='A', arguments={})))
                session.add(BrainBoxJob.from_task(BrainBoxTask(id='3', decider='B', arguments={})))
                session.commit()
            service = BrainBoxService({'A': None}, None, None, None)
            service.engine = engine
            service.remove_incorrect_tasks()
            with Session(engine) as session:
                result = list(session.execute(select(BrainBoxJob.id, BrainBoxJob.finished, BrainBoxJob.error)))
            engine.dispose()

        result = {int(z.id): z for z in result}
        self.assertTrue(result[3].finished)
        self.assertIsNotNone(result[3].error)
        for i in [1,2]:
            self.assertFalse(result[i].finished)
            self.assertIsNone(result[i].error)


