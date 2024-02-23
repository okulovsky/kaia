from dataclasses import dataclass
import os
import time
from typing import *
import requests
from ..small_classes import BrainBoxJob, BrainBoxTask, BrainBoxTaskPack, IDecider, Base, LogItem
from ..planers import SimplePlanner
from .web_server import BrainBoxEndpoints, BrainBoxWebServer
from .service import BrainBoxService
from pathlib import Path
from kaia.infra import MarshallingEndpoint, Loc, Sql
from kaia.infra.app import KaiaApp, SubprocessRunner
import uuid
from sqlalchemy.orm import Session
from threading import Thread
from sqlalchemy import select

class BrainBoxWebApi:
    def __init__(self, address, cache_folder):
        self.address = address
        self.caller = MarshallingEndpoint.Caller(address)
        self.cache_folder = cache_folder

    def add(self, task: Union[BrainBoxTaskPack, BrainBoxTask, Iterable[BrainBoxTask]]):
        if isinstance(task, BrainBoxTask):
            task = [task]
        elif isinstance(task, BrainBoxTaskPack):
            task = list(task.intermediate_tasks) + [task.resulting_task]
        self.caller.call(BrainBoxEndpoints.add, list(task))

    def execute(self, task: Union[BrainBoxTaskPack, BrainBoxTask, Iterable[BrainBoxTask]]) -> Any:
        self.add(task)
        return self.join(task)

    def join(self, task: Union[BrainBoxTaskPack, str, BrainBoxTask, Iterable[str], Iterable[BrainBoxTask]]):
        if isinstance(task, str):
            input = [task]
        elif isinstance(task, BrainBoxTask):
            input = [task.id]
        elif isinstance(task, BrainBoxTaskPack):
            input = [task.resulting_task.id]
        else:
            input = [element.id if isinstance(element, BrainBoxTask) else element for element in task]
        output = self.caller.call(BrainBoxEndpoints.join, input)
        if isinstance(task, str) or isinstance(task, BrainBoxTask):
            return output[0]
        elif isinstance(task, BrainBoxTaskPack):
            return task.postprocessor.postprocess(output[0], self)
        else:
            return output

    def get_summary(self, batch: Optional[str] = None) -> List[Dict]:
        return self.caller.call(BrainBoxEndpoints.summary, batch)

    def get_job(self, id) -> BrainBoxJob:
        return self.caller.call(BrainBoxEndpoints.job, id)

    def get_result(self, id) -> Any:
        return self.caller.call(BrainBoxEndpoints.result, id)

    def get_file(self, fname):
        response = requests.get(f'http://{self.caller.address}/file/{fname}')
        if response.status_code!=200:
            raise ValueError(response.text)
        return response.content

    def download(self, fname, custom_file_path: Optional[Path] = None, replace: bool = False) -> Path:
        if custom_file_path is None:
            custom_file_path = self.cache_folder/fname
        os.makedirs(custom_file_path.parent, exist_ok=True)
        if custom_file_path.is_file():
            if not replace:
                return custom_file_path
        data = self.get_file(fname)
        with open(custom_file_path, 'wb') as file:
            file.write(data)
            file.flush()
        return custom_file_path





    def is_available(self) -> bool:
        try:
            reply = requests.get('http://'+self.address, timeout=0.5)
            return True
        except:
            return False


class BrainBoxTestApi:
    def __init__(self, services, cache_folder = None, address = '127.0.0.1:8099'):
        if cache_folder is None:
            cache_folder = Loc.temp_folder / 'tests/brainboxwebservicetextfilecache'
        self.cache_folder = cache_folder
        self.address = address
        self.services = services

    def __enter__(self):
        service = BrainBoxService(
            self.services,
            SimplePlanner(),
            self.cache_folder,
        )
        server = BrainBoxWebServer(8099, Sql.test_file('brainbox_web_test_db_' + str(uuid.uuid4())), self.cache_folder, service)
        self.app = KaiaApp()
        self.app.add_runner(SubprocessRunner(server, 5))
        self.app.run_services_only()

        api = BrainBoxWebApi(self.address, self.cache_folder)
        return api

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.app.exit()

    @staticmethod
    def execute_serverless(
                tasks: List[BrainBoxTask],
                services: Dict[str, IDecider],
                folder: Optional[Path] = None
        ) -> tuple[list[BrainBoxJob],list[str]]:

        jobs = [BrainBoxJob.from_task(t) for t in tasks]
        sql = Sql.test_file('service' + str(uuid.uuid4()))
        engine = sql.engine()
        Base.metadata.create_all(engine)

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






