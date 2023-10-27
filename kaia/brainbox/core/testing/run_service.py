from typing import *
import uuid

from ....infra.comm import Sql
from ....infra import Loc
from .. import LogItem, BrainBoxService, BrainBoxJob, BrainBoxTask, SimplePlanner, IDecider
from ..job import Base

from threading import Thread
import time
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

class Logger:
    def __init__(self):
        self.buffer = []

    def __call__(self, item: LogItem):
        #print(f'{item.level} {item.id} {item.event}')
        self.buffer.append(item)



def run_service(tasks: List[BrainBoxTask], services: Dict[str, IDecider]):
    jobs = [BrainBoxJob.from_task(t) for t in tasks]
    sql = Sql.test_file('service'+str(uuid.uuid4()))
    engine = sql.engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(jobs)
        session.commit()

    log = Logger()
    folder = Loc.temp_folder/'tests/brainboxtextfilecache'

    service = BrainBoxService(
        services,
        SimplePlanner(),
        folder,
        log
    )
    thread = Thread(target=service.cycle, args=[engine, sql.messenger()])
    thread.start()
    while True:
        with Session(engine) as session:
            cnt = sum(session.scalars(select(BrainBoxJob.finished)))
            print(f'*** {cnt}')
            if cnt == len(tasks):
                break
            time.sleep(0.5)
    service.terminate()
    thread.join()
    with Session(engine) as session:
        finished_tasks = list(session.scalars(select(BrainBoxJob)))
    return finished_tasks, log
