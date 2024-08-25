import time
from typing import *

import pandas as pd
import os

from .service import BrainBoxService
from ..small_classes import BrainBoxJob, BrainBoxBase, BrainBoxTask
import flask
from kaia.infra.comm import IComm
import io
from pathlib import Path
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from threading import Thread
import logging
from kaia.infra import MarshallingEndpoint
from datetime import timedelta

class BrainBoxEndpoints:
    add = MarshallingEndpoint('/add', 'POST')
    join = MarshallingEndpoint('/join', 'POST')
    summary = MarshallingEndpoint('/summary', 'GET')
    job = MarshallingEndpoint('/job','GET')
    result = MarshallingEndpoint('/result', 'GET')


class BrainBoxWebServer:
    def __init__(self,
                 port: int,
                 comm: IComm,
                 file_cache: Path,
                 brainbox: Optional[BrainBoxService],
                 ):
        self.port = port
        self.comm = comm
        self.file_cache = file_cache
        self.brainbox = brainbox
        self.brainbox_thread = None #type: Optional[Thread]
        self.engine = None #type: Optional[Engine]



    def __call__(self):
        self.engine = self.comm.engine()
        BrainBoxJob.metadata.create_all(self.engine)
        if self.brainbox is not None:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
            messenger = self.comm.messenger()
            self.brainbox_thread = Thread(target=self.brainbox.cycle, args=[self.engine, messenger])
            self.brainbox_thread.start()

        self.app = flask.Flask('brainbox')
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/status', view_func=self.status, methods=['GET'])
        self.app.add_url_rule('/file/<fname>', view_func=self.file, methods=['GET'])
        self.app.add_url_rule('/cancel/<id>', view_func=self.cancel, methods=['GET'])
        self.app.add_url_rule('/cancel-all', view_func=self.cancel_all, methods=['GET'])
        self.app.add_url_rule('/upload', view_func=self.upload, methods=['POST'])

        binder = MarshallingEndpoint.Binder(self.app)
        binder.bind_all(BrainBoxEndpoints, self)

        self.app.run('0.0.0.0',self.port)

    def index(self):
        df = pd.DataFrame(self.summary(None))
        if df.shape[0]!=0:
            df = df.sort_values('received_timestamp', ascending=False)
        df = df.reset_index(drop=True)
        return df.to_html()

    def status(self):
        return 'OK'


    def file(self, fname):
        with open(self.file_cache/fname, 'rb') as file:
            return flask.send_file(
                io.BytesIO(file.read()),
                mimetype='application/octet-stream'
            )

    def terminate(self):
        if self.brainbox is not None:
            self.brainbox.terminate()
        os._exit(0)


    def cancel(self, id: str):
        self.brainbox.cancel(id)
        return 'OK'

    def cancel_all(self):
        with Session(self.engine) as session:
            jobs = list(session.scalars(select(BrainBoxJob).where(~BrainBoxJob.finished)))
            for job in jobs:
                self.cancel(job.id)
        return "OK"


    def add(self, tasks: List[BrainBoxTask]):
        with Session(self.engine) as session:
            for i, task in enumerate(tasks):
                job = BrainBoxJob.from_task(task)
                job.received_timestamp+=timedelta(microseconds=i)
                session.add(job)
            session.commit()


    def join(self, ids: List[str]):
        while True:
            with Session(self.engine) as session:
                jobs: List[BrainBoxJob] = list(session.scalars(select(BrainBoxJob).where(BrainBoxJob.id.in_(ids))))
            if len(jobs) != len(ids):
                missing = list(set(ids) - set(j.id for j in jobs))
                raise ValueError(f'Join_execute is missing jobs for ids {missing}')
            id_to_job = {}
            for job in jobs:
                if not job.finished:
                    break
                if not job.success:
                    stars='*~'*30
                    raise ValueError(f"{job.decider}/{job.decider_parameters} threw an error:\n{stars}\n{job.error}\n{stars}")
                id_to_job[job.id] = job
            if len(id_to_job) == len(ids):
                return [id_to_job[id].result for id in ids]
            time.sleep(0.01)


    def summary(self, batch: Optional[str] = None):
        with Session(self.engine) as session:
            query = select(
                BrainBoxJob.id,
                BrainBoxJob.decider,
                BrainBoxJob.method,
                BrainBoxJob.batch,
                BrainBoxJob.back_track,
                BrainBoxJob.received_timestamp,
                BrainBoxJob.ready,
                BrainBoxJob.ready_timestamp,
                BrainBoxJob.assigned,
                BrainBoxJob.assigned_timestamp,
                BrainBoxJob.accepted,
                BrainBoxJob.accepted_timestamp,
                BrainBoxJob.finished,
                BrainBoxJob.finished_timestamp,
                BrainBoxJob.success,
                BrainBoxJob.error,
            )
            if batch is not None:
                query = query.where(BrainBoxJob.batch == batch)
            rows = list(dict(r._mapping) for r in session.execute(query))
        return rows


    def job(self, id):
        with Session(self.engine) as session:
            result = list(session.scalars(select(BrainBoxJob).where(BrainBoxJob.id == id)))
            if len(result)==0:
                return None
            record = result[0]
            session.expunge(record)
        return record


    def result(self, id):
        with Session(self.engine) as session:
            result = list(session.scalars(select(BrainBoxJob.result).where(BrainBoxJob.id == id)))
        if len(result)==0:
            return None
        return result[0]

    def upload(self):
        for key, value in flask.request.files.items():
            value.save(self.file_cache/key)
        return 'OK'


