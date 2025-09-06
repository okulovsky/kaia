from sqlalchemy import Column, Integer, String, JSON, Index, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class MessageRecord(Base):
    __tablename__ = 'message_records'
    __table_args__ = (
        # индекс по message_id для быстрого поиска
        Index('ix_message_records_message_id', 'message_id'),
        UniqueConstraint('message_id', name='uq_message_records_message_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, nullable=False)
    message_type = Column(String, nullable=False)
    session = Column(String, nullable=True)
    envelop = Column(JSON, nullable=False)
    payload = Column(JSON, nullable=False)

    def to_dict(self):
        return {
            'message_type': self.message_type,
            'session': self.session,
            'envelop': self.envelop,
            'payload': self.payload,
        }