import os
import uuid

import flask
from .components import IAvatarComponent
from pathlib import Path
from .message_record import MessageRecord, Base
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from .serialization import get_full_name_by_type
import uuid

class MessagingComponent(IAvatarComponent):
    def __init__(self, db_path: Path, aliases: dict[str, type] = None):
        self.db_path = db_path
        if aliases is None:
            aliases = {}
        self.aliases = aliases

    def setup_server(self, app: flask.Flask):
        os.makedirs(self.db_path.parent, exist_ok=True)
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, future=True)
        app.add_url_rule('/messages/add', view_func=self.messages_add, methods=['POST'])
        app.add_url_rule('/messages/get', view_func=self.messages_get, methods=['GET'])

    def messages_add(self):
        data = flask.request.get_json(force=True)

        for field in ('message_type', 'envelop', 'payload'):
            if field not in data:
                return flask.jsonify({'error': f'Missing field: {field}'}), 400

        if data['message_type'] in self.aliases:
            data['message_type'] = get_full_name_by_type(self.aliases[data['message_type']])

        if 'id' not in data['envelop'] or data['envelop']['id'] is None:
            data['envelop']['id'] = str(uuid.uuid4())

        msg = MessageRecord(
            message_id=data['envelop']['id'],
            message_type=data['message_type'],
            session=data.get('session'),
            envelop=data['envelop'],
            payload=data['payload']
        )

        with self.Session() as db:
            db.add(msg)
            db.commit()
            db.refresh(msg)

        return "OK"

    def messages_get(self):
        session_param = flask.request.args.get('session', default=None, type=str)
        last_message_id = flask.request.args.get('last_message_id', default=None, type=str)
        count = flask.request.args.get('count', default=None, type=int)

        with self.Session() as db:
            q = db.query(MessageRecord)

            if session_param is not None:
                q = q.filter(MessageRecord.session == session_param)

            if last_message_id is not None:
                last = (
                    db.query(MessageRecord)
                    .filter(MessageRecord.message_id == last_message_id)
                    .first()
                )
                if last:
                    q = q.filter(MessageRecord.id > last.id)
                else:
                    return flask.jsonify({'error': 'last_message_id not found'}), 400

            q = q.order_by(asc(MessageRecord.id))

            if count is not None:
                q = q.limit(count)

            results = q.all()
            return flask.jsonify([msg.to_dict() for msg in results]), 200



