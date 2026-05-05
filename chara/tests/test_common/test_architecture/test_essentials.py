from unittest import TestCase
from chara.common.architecture.function_to_name import function_to_name

class MyPipeline:
    def __call__(self):
        return

    def instance_method(self):
        return

    @classmethod
    def class_method(cls):
        return

    @staticmethod
    def static_method():
        return


def my_function():
    return

class FunctionNameTestCase(TestCase):
    def test_function(self):
        self.assertEqual('my_function', function_to_name(my_function))

    def test_pipeline(self):
        self.assertEqual('MyPipeline', function_to_name(MyPipeline()))

    def test_instance_method(self):
        self.assertEqual('MyPipeline-instance_method', function_to_name(MyPipeline().instance_method))

    def test_class_method(self):
        self.assertEqual('MyPipeline-class_method', function_to_name(MyPipeline().class_method))

    def test_static_method(self):
        self.assertEqual('MyPipeline-static_method', function_to_name(MyPipeline.static_method))

    def test_lambda(self):
        self.assertEqual('lambda', function_to_name(lambda _: _+1))
