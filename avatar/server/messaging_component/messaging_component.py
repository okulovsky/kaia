import os
import flask
from ..components import IAvatarComponent
from pathlib import Path
from .message_record import MessageRecord, Base
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
import uuid
from foundation_kaia.misc import Loc
from ...messaging import IMessage
from .message_format import MessageFormat, get_full_name_by_type

class MessagingComponent(IAvatarComponent):
    def __init__(self,
                 db_path: Path|None = None,
                 aliases: dict[str, type] = None,
                 session_to_initialization_messages: dict[str,tuple[IMessage,...]]|None = None,
                 ):
        self.db_path = db_path
        if self.db_path is None:
            self.db_path = Loc.temp_folder/'avatar_debug_db'
            if self.db_path.is_file():
                os.unlink(self.db_path)
        if aliases is None:
            aliases = {}
        self.aliases = aliases
        self.session_to_initialization_messages = session_to_initialization_messages

    def setup_server(self, app: IAvatarComponent.App, address: str):
        os.makedirs(self.db_path.parent, exist_ok=True)
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, future=True)
        app.add_url_rule('/messages/add', view_func=self.messages_add, methods=['POST'])
        app.add_url_rule('/messages/get', view_func=self.messages_get, methods=['GET'])
        app.add_url_rule('/messages/last', view_func=self.messages_last, methods=['GET'])
        if self.session_to_initialization_messages is not None:
            for session, messages in self.session_to_initialization_messages.items():
                for message in messages:
                    js = MessageFormat.to_json(message, session)
                    self._add_message(js)

    def _add_message(self, data):
        for field in ('message_type', 'envelop', 'payload'):
            if field not in data:
                raise ValueError(f'Missing field: {field}')

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



    def messages_add(self):
        data = flask.request.get_json(force=True)
        try:
            self._add_message(data)
        except ValueError as ex:
            return flask.jsonify({'error': ex.args[0]})
        return "OK"


    def messages_last(self):
        session_param = flask.request.args.get('session', default=None, type=str)

        with self.Session() as db:
            q = db.query(MessageRecord)

            if session_param is not None:
                q = q.filter(MessageRecord.session == session_param)

            last_message = (
                q
                .order_by(MessageRecord.id.desc())
                .first()
            )

            id = None if last_message is None else last_message.message_id
            return flask.jsonify({'id': id})


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



