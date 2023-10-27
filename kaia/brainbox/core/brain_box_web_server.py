import uuid
from typing import *

import pandas as pd
import os

from .brain_box_service import BrainBoxService
from .job import BrainBoxJob, Base
import json
import flask
import jsonpickle
from kaia.infra.comm import IComm
import io
from pathlib import Path
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from threading import Thread
from datetime import datetime
import jsonpickle
import logging

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
        Base.metadata.create_all(self.engine)
        if self.brainbox is not None:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
            messenger = self.comm.messenger()
            self.brainbox_thread = Thread(target=self.brainbox.cycle, args=[self.engine, messenger])
            self.brainbox_thread.start()

        self.app = flask.Flask('brainbox')
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/add/<decider>/<method>', view_func=self.add, methods=['POST'])
        self.app.add_url_rule('/jobs/', view_func=self.jobs, methods=['GET'], defaults = {'batch': None})
        self.app.add_url_rule('/jobs/<batch>', view_func=self.jobs, methods=['GET'])
        self.app.add_url_rule('/job/<id>', view_func=self.job, methods=['GET'])
        self.app.add_url_rule('/result/<id>', view_func=self.result, methods=['GET'])
        self.app.add_url_rule('/file/<fname>', view_func=self.file, methods=['GET'])
        self.app.add_url_rule('/cancel/<id>', view_func=self.cancel, methods=['POST'])

        self.app.run('0.0.0.0',self.port)

    def index(self):
        df = pd.DataFrame(self._get_jobs(None))
        if df.shape[0]!=0:
            df = df.sort_values('received_timestamp', ascending=False)
        return df.to_html()


    def add(self, decider: str, method: str):
        request = flask.request.json
        arguments = request['arguments']
        id = request.get('id', None)
        if id is None:
            id = str(uuid.uuid4())
        dependencies = request.get('dependencies', None)
        back_track = request.get('back_track', None)
        batch = request.get('batch', None)

        task = BrainBoxJob(
            id = id,
            batch = batch,
            decider = decider,
            method = method,
            arguments = arguments,
            dependencies = dependencies,
            back_track = back_track,
            received_timestamp = datetime.now()
        )

        with Session(self.engine) as session:
            session.add(task)
            session.commit()

        return flask.jsonify(id)

    def _get_jobs(self, batch):
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

    def jobs(self, batch):
        print(f'Batch: {batch}')
        jobs = self._get_jobs(batch)
        return flask.jsonify(json.loads(jsonpickle.dumps(jobs)))

    def job(self, id):
        with Session(self.engine) as session:
            result = list(session.scalars(select(BrainBoxJob).where(BrainBoxJob.id == id)))
        if len(result)==0:
            return flask.jsonify(None)
        record = result[0].__dict__
        del record['_sa_instance_state']
        return flask.jsonify(record)

    def result(self, id):
        with Session(self.engine) as session:
            result = list(session.scalars(select(BrainBoxJob.result).where(BrainBoxJob.id == id)))
        if len(result)==0:
            return flask.jsonify(None)
        return flask.jsonify(result[0])


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