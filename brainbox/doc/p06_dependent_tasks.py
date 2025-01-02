from brainbox import BrainBox
from brainbox.deciders import Boilerplate
from unittest import TestCase

def dependent_tasks(test_case: TestCase, api: BrainBox.Api):
    """
    ### Build a workflow from tasks

    The output of the tasks can serve as an input to other tasks:
    """
    task1 = BrainBox.Task.call(Boilerplate).json("Hello")
    task2 = BrainBox.Task.call(Boilerplate).json(task1)
    result = api.execute([task1, task2])
    test_case.assertDictEqual(result[0], result[1]['argument'])

    """
    In this case, the `task1` will be executed before `task2` and the output of `task1` will be used
    as an argument for `task2` method.
    """

def collector(test_case: TestCase, api: BrainBox.Api):
    """
    ### Collect the outputs of many tasks

    One particularly important use case of the dependent tasks is when
    several tasks are run, each associated with some __tags__ describing a task,
    and then the outputs of all tasks are collected together and returned as a single entity.

    `Collector` does just this. Declaring collector tasks in a raw form is very cumbersome,
     and we actually use helpers to do this,
     however, it helps to see what's going on under the hood.
    """
    from brainbox.deciders import Collector
    from brainbox import BrainBoxCombinedTask

    id1 = BrainBox.Task.safe_id()
    id2 = BrainBox.Task.safe_id()
    task1 = BrainBox.Task.call(Boilerplate).json(0).to_task(id=id1)
    task2 = BrainBox.Task.call(Boilerplate).json(1).to_task(id=id2)
    collector = BrainBox.Task.call(Collector).to_array(
        tags = {id1: dict(index=0), id2: dict(index=1)},
        ** {
            id1: task1,
            id2: task2
        }
    )
    pack = BrainBoxCombinedTask(
        resulting_task = collector,
        intermediate_tasks = (task1, task2)
    )
    array = api.execute(pack)
    for item in array:
        test_case.assertIsNone(item['error'])
        test_case.assertEqual(item['tags']['index'], item['result']['argument'])



    """
    Method `BrainBox.Task.safe_id` creates uuid4 and converts it in python literal so it can be used in **kwargs. 
    
    We can shorten this significantly with `Collector.TaskBuilder`:
    """

    builder = Collector.TaskBuilder()
    for i in range(10):
        builder.append(task=BrainBox.Task.call(Boilerplate).json(i), tags=dict(index=i))
    pack = builder.to_collector_pack('to_array')
    array = api.execute(pack)
    for item in array:
        test_case.assertIsNone(item['error'])
        test_case.assertEqual(item['tags']['index'], item['result']['argument'])


def media_library(test_case:TestCase, api:BrainBox.Api):
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
    for i in range(10):
        builder.append(task=BrainBox.Task.call(Boilerplate).file(i), tags=dict(index=i))
    pack = builder.to_collector_pack('to_media_library')
    path = api.download(api.execute(pack))
    ml = MediaLibrary.read(path)
    for record in ml.records:
        content = record.get_content()
        tags = record.tags
        test_case.assertEqual(tags['index'], json.loads(content)['argument'])




