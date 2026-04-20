from foundation_kaia.releasing.mddoc import *

"""
### Serialization

`foundation_kaia` uses its own serialization, that allows you to convert to and from JSON complex data structures.
Depending on the type annotations, `str` can be deserialized to a string, a timestamp, an Enum and so on.
`dict` can be deserialized to a dictionary, a dataclass or a sqlalchemy record.

The entry point is `Serializer.parse(type)`, which builds a serializer for any supported type.
Call `.to_json(value)` to produce a JSON-compatible value and `.from_json(json_value)` to restore the
original Python object.

There are several extensions for the plain JSON objects that are supported in this module.

#### Dataclasses

"""

from dataclasses import dataclass
from foundation_kaia.marshalling import Serializer

@dataclass
class Point:
    x: int
    y: int

point_result = ControlValue.mddoc_define_control_value(Point(x=1, y=2))
point_list_result = ControlValue.mddoc_define_control_value([Point(x=1, y=2), Point(x=3, y=4)])

if __name__ == '__main__':
    point = Serializer.parse(Point).from_json({'x': 1, 'y': 2})

    """
    The parsed value is:
    """
    point_result.mddoc_validate_control_value(point)

    point_list = Serializer.parse(list[Point]).from_json([{'x': 1, 'y': 2}, {'x': 3, 'y': 4}])

    """
    The parsed list is:
    """
    point_list_result.mddoc_validate_control_value(point_list)

"""

#### Additional primitives

Enums, datetime and Path are serialized as strings and deserialized as the objects of the corresponding type.
Enums are serialized and deserialized by their **name**, not their value.

"""
from enum import Enum
from datetime import datetime
from pathlib import Path

class Color(Enum):
    RED = 'red'
    GREEN = 'green'

@dataclass
class Event:
    color: Color
    when: datetime
    log_path: Path

event_result = ControlValue.mddoc_define_control_value(Event(Color.GREEN, datetime(2025, 1, 15, 12, 0, 0), Path('/var/log/app.log')))

if __name__ == '__main__':
    event = Serializer.parse(Event).from_json({
        "color": "GREEN",
        "when": "2025-01-15T12:00:00",
        "log_path": "/var/log/app.log",
    })

    """
    The deserialized value is:
    """
    event_result.mddoc_validate_control_value()

"""

#### Bytes

Bytes fields are serialized as a tagged object with a base-64 encoded value.

"""

@dataclass
class Blob:
    name: str
    content: bytes

blob_result = ControlValue.mddoc_define_control_value(Blob(name='file.bin', content=b'\x00\x01\x02\x03'))

if __name__ == '__main__':
    blob = Serializer.parse(Blob).from_json({'name': 'file.bin', 'content': {'@type': 'bytes', 'value': 'AAECAw=='}})

    """
    The parsed value is:
    """
    blob_result.mddoc_validate_control_value(blob)

"""

#### SQLAlchemy entities

SQLAlchemy mapped classes are serialized and deserialized using their column attributes.

"""

from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()

class UserRecord(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    score: Mapped[float | None] = mapped_column(nullable=True)

user_result = ControlValue.mddoc_define_control_value({'id': 1, 'name': 'alice', 'score': 9.5})

if __name__ == '__main__':
    user = Serializer.parse(UserRecord).from_json({'id': 1, 'name': 'alice', 'score': 9.5})

    """
    The parsed fields are:
    """
    user_result.mddoc_validate_control_value({'id': user.id, 'name': user.name, 'score': user.score}, )

"""

#### Polymorphism

When a dataclass field is typed as a base class but holds a subclass at runtime, the serializer
adds `@type` and `@subtype` tags so the exact subclass can be reconstructed on deserialization.
When the field holds an exact instance of the declared type, no extra tags are added.

"""

@dataclass
class Shape:
    color: str

@dataclass
class Circle(Shape):
    radius: float

@dataclass
class Canvas:
    title: str
    background: Shape

from foundation_kaia.marshalling.serialization.tools import TypeTools

canvas_bg_type_result = ControlValue.mddoc_define_control_value("Circle")

if __name__ == '__main__':
    canvas = Serializer.parse(Canvas).from_json({
        'title': 'art',
        'background': {
            '@type': 'dataclass',
            '@subtype': TypeTools.type_to_full_name(Circle),
            'color': 'red',
            'radius': 5.0,
        },
    })

    """
    The background field is reconstructed as the exact subclass; its type name is:
    """
    canvas_bg_type_result.mddoc_validate_control_value(type(canvas.background).__name__)

"""

#### Unsupported data

In case the type is not supported, it will be serialized with pickle and passed as base-64 encoded bytes.
This allows the serialization/deserialization in itself to be complete and handle the cases that are not covered by supported types.
So, if you want to keep your endpoints compatible with non-python APIs, you need to use only the supported types in them.
"""
