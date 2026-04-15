import unittest
from datetime import datetime
from typing import Optional, List

from foundation_kaia.marshalling.serialization.handlers.type_handler import SerializationContext
from foundation_kaia.marshalling.serialization.handlers.sqlalchemy_handler import SqlalchemyHandler

try:
    from sqlalchemy.orm import declarative_base, Mapped, mapped_column
    from sqlalchemy import JSON
    sqlalchemy_available = True
except ImportError:
    sqlalchemy_available = False


def _ctx():
    return SerializationContext(path=[], allow_base64=True)


@unittest.skipUnless(sqlalchemy_available, "sqlalchemy not installed")
class TestSqlalchemyHandler(unittest.TestCase):

    def setUp(self):
        Base = declarative_base()

        class SampleModel(Base):
            __tablename__ = "sample"

            id: Mapped[str] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column()
            count: Mapped[int] = mapped_column()
            score: Mapped[Optional[float]] = mapped_column(nullable=True)
            active: Mapped[bool] = mapped_column()
            created_at: Mapped[datetime] = mapped_column()
            tags: Mapped[Optional[List[str]]] = mapped_column(type_=JSON, nullable=True)

        self.SampleModel = SampleModel
        self.handler = SqlalchemyHandler(SampleModel)

    def _make_instance(self, **overrides):
        defaults = dict(
            id="abc-123",
            name="test",
            count=42,
            score=3.14,
            active=True,
            created_at=datetime(2024, 6, 1, 12, 0, 0),
            tags=["a", "b"],
        )
        defaults.update(overrides)
        return self.SampleModel(**defaults)

    def test_round_trip(self):
        obj = self._make_instance()
        json_data = self.handler.to_json(obj, _ctx())
        restored = self.handler.from_json(json_data, _ctx())
        for field in self.handler.fields:
            self.assertEqual(getattr(obj, field), getattr(restored, field))

    def test_json_structure(self):
        obj = self._make_instance(name="hello", count=7, score=None, tags=None)
        json_data = self.handler.to_json(obj, _ctx())
        self.assertEqual(json_data["name"], "hello")
        self.assertEqual(json_data["count"], 7)
        self.assertIsNone(json_data["score"])
        self.assertIsNone(json_data["tags"])
        self.assertIn("created_at", json_data)

    def test_parse_detects_model(self):
        result = SqlalchemyHandler.parse(self.SampleModel, None, None)
        self.assertIsInstance(result, SqlalchemyHandler)

    def test_parse_rejects_non_model(self):
        result = SqlalchemyHandler.parse(int, None, None)
        self.assertIsNone(result)

    def test_nullable_round_trip(self):
        obj = self._make_instance(score=None, tags=None)
        json_data = self.handler.to_json(obj, _ctx())
        restored = self.handler.from_json(json_data, _ctx())
        self.assertIsNone(restored.score)
        self.assertIsNone(restored.tags)
