from .message_record import MessageRecord
from .message_store import IMessageStore, LastMessageNotFoundException
from sqlalchemy import asc, or_, and_

class SqlMessageStore(IMessageStore):
    def __init__(self, session_maker):
        self.Session = session_maker

    def add(self, msg: MessageRecord) -> None:
        with self.Session() as db:
            db.add(msg)
            db.commit()
            db.refresh(msg)
            db.expunge(msg)


    def last_id(self, session: str|None) -> str|None:
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
            return id

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


    def tail(self,
             session: str|None,
             count: int|None,
             types: list[str]|None,
             except_types: list[str]|None
             ) -> list[MessageRecord]:
        with self.Session() as db:
            q = self._get_query_essentials(db, session, types, except_types)
            result = (
                q.order_by(MessageRecord.id.desc())
                .limit(count)
                .all()
            )
            result = list(reversed(result))
            return result

    def get(self,
            session: str|None,
            count: int|None,
            last_message_id: str|None,
            types: list[str]|None,
            except_types: list[str]|None) -> list[MessageRecord]:
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
                    raise LastMessageNotFoundException(last_message_id)

            q = q.order_by(asc(MessageRecord.id))
            if count is not None:
                q = q.limit(count)

            results = q.all()
            return results


