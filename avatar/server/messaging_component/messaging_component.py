import os
import flask
from ..components import IAvatarComponent
from pathlib import Path
from .store import MessageRecord, Base, SqlMessageStore, IMessageStore, LastMessageNotFoundException
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker
import uuid
from foundation_kaia.misc import Loc
from ...messaging import IMessage
from .message_format import MessageFormat, get_full_name_by_type
from typing import Type, Callable, Any, Optional
from threading import Thread
from datetime import datetime, timedelta
import time


import  importlib, pkgutil, inspect

class MessagingComponent(IAvatarComponent):
    def __init__(self,
                 db_path: Path|None = None,
                 aliases: dict[str, type] = None,
                 session_to_initialization_messages: dict[str,tuple[IMessage,...]]|None = None,
                 cleanup_time_in_seconds_to_message_types: dict[float, tuple[Type[IMessage],...]]|None = None,
                 store_factory: Optional[Callable[[Any], IMessageStore]] = None
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
        self.cleanup_time_in_seconds_to_message_types = cleanup_time_in_seconds_to_message_types
        self.store_factory = store_factory


    def _cleanup(self):
        min_cleanup_time = min(self.cleanup_time_in_seconds_to_message_types)
        while True:
            with self.Session() as session:
                for ttl, messages in self.cleanup_time_in_seconds_to_message_types.items():
                    cutoff = datetime.now() - timedelta(seconds=ttl)
                    type_names = [get_full_name_by_type(t) for t in messages]
                    stmt = (
                        delete(MessageRecord)
                        .where(MessageRecord.message_type.in_(type_names))
                        .where(MessageRecord.created_at < cutoff)
                    )
                    session.execute(stmt)
                session.commit()
            time.sleep(min_cleanup_time)


    def setup_server(self, app: IAvatarComponent.App, address: str):
        os.makedirs(self.db_path.parent, exist_ok=True)
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False, future=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, future=True)

        if self.store_factory is None:
            self.store = SqlMessageStore(self.Session)
        else:
            self.store = self.store_factory(self.Session)

        if self.cleanup_time_in_seconds_to_message_types is not None:
            thread = Thread(target=self._cleanup, daemon=True)
            thread.start()

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
            payload=data['payload'],
            created_at=datetime.now(),
        )
        self.store.add(msg)


    def messages_add(self):
        data = flask.request.get_json(force=True)
        self._add_message(data)
        return "OK"


    def messages_last(self):
        session = flask.request.json.get('session', None)
        id = self.store.last_id(session)
        return flask.jsonify({'id': id})

    def messages_tail(self):
        session = flask.request.json.get('session', None)
        count = flask.request.json.get('count', None)
        types = flask.request.json.get('types', None)
        except_types = flask.request.json.get('except_types', None)
        tail = self.store.tail(session, count, types, except_types)
        return flask.jsonify([msg.to_dict() for msg in tail]), 200

    def messages_get(self):
        session = flask.request.json.get('session', None)
        count = flask.request.json.get('count', None)
        last_message_id = flask.request.json.get('last_message_id', None)
        types = flask.request.json.get('types', None)
        except_types = flask.request.json.get('except_types', None)

        try:
            messages = self.store.get(session, count, last_message_id, types, except_types)
        except LastMessageNotFoundException:
            return flask.jsonify({'error': 'last_message_id not found'}), 400
        return flask.jsonify([msg.to_dict() for msg in messages]), 200

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