from brainbox.deciders import Piper
from brainbox.framework import Job, BrainBox, BrainBoxBase
from unittest import TestCase
import pickle
from foundation_kaia.marshalling_2 import Annotation

class MyFactory:
    def generate(self) -> BrainBox.Task:
        return Piper.new_task().voiceover('test')

class ObjectsSerializationTestCase(TestCase):
    def _check(self, obj):
        pickle.loads(pickle.dumps(obj))

    def test_entry_point_serialization(self):
        self._check(Piper)

    def task_factory_serialization(self):
        self._check(MyFactory())

    def test_jobs_serialization(self):
        job = Job()
        self._check(job)

    def test_brainbox_base(self):
        self._check(BrainBoxBase)

    def test_job_type(self):
        self._check(Job)

    def test_job_type_annotation(self):
        annotation = Annotation.parse(Job)
        self._check(annotation)

    def test_api(self):
        api = BrainBox.Api('127.0.0.1')
        self._check(api)