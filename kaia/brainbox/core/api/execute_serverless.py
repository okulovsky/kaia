import time
from typing import *
from ..small_classes import BrainBoxJob, BrainBoxTask, IDecider, BrainBoxBase, LogItem
from ..planers import SimplePlanner, AlwaysOnPlanner
from .service import BrainBoxService
from pathlib import Path
from kaia.infra import MarshallingEndpoint, Loc, Sql
import uuid
from sqlalchemy.orm import Session
from threading import Thread
from sqlalchemy import select


def execute_serverless(
        tasks: List[BrainBoxTask],
        services: Dict[str, IDecider],
        folder: Optional[Path] = None
) -> tuple[list[BrainBoxJob], list[str]]:
    jobs = [BrainBoxJob.from_task(t) for t in tasks]
    sql = Sql.test_file('service' + str(uuid.uuid4()))
    engine = sql.engine()
    BrainBoxBase.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all(jobs)
        session.commit()

    class Logger:
        def __init__(self):
            self.buffer = []

        def __call__(self, item: LogItem):
            # print(f'{item.level} {item.id} {item.event}')
            self.buffer.append(item)

    loger = Logger()
    if folder is None:
        folder = Loc.temp_folder / 'tests/brainboxtextfilecache'

    service = BrainBoxService(
        services,
        SimplePlanner(),
        folder,
        loger
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
    return finished_tasks, loger.buffer


