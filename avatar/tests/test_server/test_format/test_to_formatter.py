from unittest import TestCase
from avatar.server.messaging_component.format.custom_formatters import *
from avatar.server.messaging_component.format.dataclass_formatter import *
from avatar.server.messaging_component.format.default_formatter import *
from avatar.server.messaging_component.format import Format

class TestToFormatter(TestCase):
    def test_primitive_types(self):
        for prim in (int, bool, str):
            fmt = Format.get_formatter(prim)
            self.assertIsInstance(fmt, PrimitiveFormatter)
            self.assertTrue(fmt.not_null)

    def test_float(self):
        fmt = Format.get_formatter(float)
        self.assertIsInstance(fmt, FloatFormatter)

    def test_enum(self):
        class Color(Enum):
            RED = 1
            GREEN = 2

        fmt = Format.get_formatter(Color)
        self.assertIsInstance(fmt, EnumFormatter)
        self.assertEqual(fmt._type, Color)

    def test_dataclass(self):
        @dataclass
        class Point:
            x: int
            y: int

        fmt = Format.get_formatter(Point)
        self.assertIsInstance(fmt, DataClassFormatter)
        self.assertEqual(fmt._type, Point)

    def test_bare_list_and_tuple(self):
        # без generic-параметров
        fmt_list = Format.get_formatter(list)
        self.assertIsInstance(fmt_list, ListFormatter)
        self.assertIsInstance(fmt_list.element_formatter, DefaultFormatter)

        fmt_tuple = Format.get_formatter(tuple)
        self.assertIsInstance(fmt_tuple, TupleFormatter)
        self.assertIsInstance(fmt_tuple.element_formatter, DefaultFormatter)

    def test_list_of_int(self):
        fmt = Format.get_formatter(list[int])
        self.assertIsInstance(fmt, ListFormatter)
        self.assertIsInstance(fmt.element_formatter, PrimitiveFormatter)
        self.assertEqual(fmt.element_formatter._type, int)

    def test_tuple_of_str(self):
        fmt = Format.get_formatter(tuple[str, ...])
        self.assertIsInstance(fmt, TupleFormatter)
        self.assertIsInstance(fmt.element_formatter, PrimitiveFormatter)
        self.assertEqual(fmt.element_formatter._type, str)

    def test_dict_str_to_float(self):
        fmt = Format.get_formatter(dict[str, float])
        self.assertIsInstance(fmt, DictFormatter)
        self.assertIsInstance(fmt.element_formatter, FloatFormatter)


    def test_optional_type(self):
        # Optional[int] == Union[int, None]
        OptInt = int | None
        fmt = Format.get_formatter(OptInt)
        # должен вернуть PrimitiveFormatter с флагом not_null=False
        self.assertIsInstance(fmt, PrimitiveFormatter)
        self.assertFalse(fmt.not_null)

    def test_unsupported_union(self):
        # Union[int, str] — не поддерживается, дефолт
        fmt = Format.get_formatter(int| str)
        self.assertIsInstance(fmt, DefaultFormatter)

    def test_unsupported_type(self):
        # например, set — не поддерживается
        fmt = Format.get_formatter(set[int])
        self.assertIsInstance(fmt, DefaultFormatter)
