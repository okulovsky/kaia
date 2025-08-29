import os
import traceback

import flask
from ..components import IAvatarComponent
from pathlib import Path
from .message_record import MessageRecord, Base
from sqlalchemy import create_engine, asc, or_, and_
from sqlalchemy.orm import sessionmaker
import uuid
from foundation_kaia.misc import Loc
from ...messaging import IMessage
from .message_format import MessageFormat, get_full_name_by_type

import  importlib, pkgutil, inspect

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
        app.add_url_rule('/messages/get', view_func=self.messages_get, methods=['POST'])
        app.add_url_rule('/messages/last', view_func=self.messages_last, methods=['POST'])
        app.add_url_rule('/messages/tail', view_func=self.messages_tail, methods=['POST'])
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
        self._add_message(data)
        return "OK"


    def messages_last(self):
        session = flask.request.json.get('session', None)
        with self.Session() as db:
            q = db.query(MessageRecord)
            if session is not None:
                q = q.filter(MessageRecord.session == session)
            last_message = (
                q
                .order_by(MessageRecord.id.desc())
                .first()
            )
            id = None if last_message is None else last_message.message_id
            return flask.jsonify({'id': id})



    def _get_type_filters(self, types: list[str]|None):
        if types is None or len(types) == 0:
            return None
        return or_(*[MessageRecord.message_type.like(f"%{suf}") for suf in types])

    def _get_except_type_filters(self, except_types: list[str]|None):
        if except_types is None or len(except_types) == 0:
            return None
        return and_(*[~MessageRecord.message_type.like(f"%{suf}") for suf in except_types])

    def _get_query_essentials(self, db, session: str|None, types: list[str]|None, except_types: list[str]|None):
        q = db.query(MessageRecord)
        if session is not None:
            q = q.filter(MessageRecord.session == session)
        type_filter = self._get_type_filters(types)
        if type_filter is not None:
            q = q.filter(type_filter)
        except_type_filter = self._get_except_type_filters(except_types)
        if except_type_filter is not None:
            q = q.filter(except_type_filter)
        return q

    def messages_tail(self):
        session = flask.request.json.get('session', None)
        count = flask.request.json.get('count', None)
        types = flask.request.json.get('types', None)
        except_types = flask.request.json.get('except_types', None)

        with self.Session() as db:
            q = self._get_query_essentials(db, session, types, except_types)
            results = (
                q.order_by(MessageRecord.id.desc())
                .limit(count)
                .all()
            )
            return flask.jsonify([msg.to_dict() for msg in reversed(results)]), 200



    def messages_get(self):
        session = flask.request.json.get('session', None)
        count = flask.request.json.get('count', None)
        last_message_id = flask.request.json.get('last_message_id', None)
        types = flask.request.json.get('types', None)
        except_types = flask.request.json.get('except_types', None)

        with self.Session() as db:
            q = self._get_query_essentials(db, session, types, except_types)
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


    @staticmethod
    def create_aliases(*namespaces):
        all_subclasses = []
        for pkg in namespaces:
            all_subclasses.extend(find_subclasses_in_package(IMessage, pkg))
        return {c.__name__: c for c in all_subclasses}



def find_subclasses_in_package(base_class: type, package_name: str) -> list[type]:
    subclasses = []
    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue  # Пропускаем модули, которые не удаётся импортировать
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, base_class) and obj is not base_class:
                subclasses.append(obj)
    return subclasses