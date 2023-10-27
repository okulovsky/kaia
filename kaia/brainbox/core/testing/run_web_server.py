from typing import *
import uuid

from ....infra.comm import Sql
from ....infra import Loc
from ....infra.app import KaiaApp, SubprocessRunner
from .. import LogItem, BrainBoxService, BrainBoxJob, BrainBoxTask, SimplePlanner, IDecider, BrainBoxWebServer, BrainBoxWebApi
from ..job import Base

from threading import Thread
import time
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime


def run_web_server(tasks: List[BrainBoxTask], services: Dict[str, IDecider], timeout = 30):
    folder = Loc.temp_folder / 'tests/brainboxwebservicetextfilecache'

    service = BrainBoxService(
        services,
        SimplePlanner(),
        folder,
    )

    server = BrainBoxWebServer(8099, Sql.test_file('brainbox_web_test_db'), folder, service)
    app = KaiaApp()
    app.add_runner(SubprocessRunner(server, 3))
    app.run_services_only()

    api = BrainBoxWebApi('http://localhost:8099', folder)
    for task in tasks:
        api.add_task(task)

    for i in range(timeout):
        status = api.get_tasks()
        all_completed = all(t['finished'] for t in status)
        if all_completed:
            break
        print('*')

    jobs = [api.get_task(t.id) for t in tasks]
    results = [api.get_result(t.id) for t in tasks]
    app.exit()
    return jobs, results
