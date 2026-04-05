from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase

def dependent_tasks(test_case: TestCase, api: BrainBox.Api):
    """
    ### Build a workflow from tasks

    The output of a task can serve as the input to another task:
    """
    task1 = HelloBrainBox.new_task().sum(2, 4)
    task2 = HelloBrainBox.new_task().sum(task1, 10)
    result = api.execute([task1, task2])
    test_case.assertEqual(6, result[0])
    test_case.assertEqual(16, result[1])

    """
    In this case, `task1` will be executed before `task2`, and the output of
    `task1` will be used as an argument to `task2`.
    """

def collector(test_case: TestCase, api: BrainBox.Api):
    """
    ### Collect the outputs of many tasks

    One particularly important use case of the dependent tasks is when
    several tasks are run, each associated with some __tags__ describing a task,
    and then the outputs of all tasks are collected together and returned as a single entity.

    `Collector` does just this. The simplest way to use it is via `Collector.TaskBuilder`:
    """
    from brainbox.deciders import Collector

    builder = Collector.TaskBuilder()
    for i in range(10):
        builder.append(task=HelloBrainBox.new_task().sum(0, i), tags=dict(index=i))
    pack = builder.to_collector_pack('to_array')
    array = api.execute(pack)
    for item in array:
        test_case.assertIsNone(item['error'])
        test_case.assertEqual(item['tags']['index'], item['result'])


def media_library(test_case: TestCase, api: BrainBox.Api):
    """
    ### Collect the files from many tasks

    One problem remains: if deciders return files, these files won't be collected.
    To solve it, MediaLibrary structure is used. Essentially it's a zip-file
    that contains all the outputs as well as tags.

    """
    from brainbox import MediaLibrary
    from brainbox.deciders import Collector
    import json

    builder = Collector.TaskBuilder()
    for i in range(3):
        builder.append(
            task=HelloBrainBox.new_task().voiceover(str(i), HelloBrainBox.Models.google),
            tags=dict(index=i)
        )
    from pathlib import Path
    import tempfile

    pack = builder.to_collector_pack('to_media_library')
    path = api.cache.download(api.execute(pack), Path(tempfile.gettempdir()))
    ml = MediaLibrary.read(path)
    for record in ml.records:
        content = record.get_content()
        tags = record.tags
        test_case.assertEqual(str(tags['index']), json.loads(content)['text'])
