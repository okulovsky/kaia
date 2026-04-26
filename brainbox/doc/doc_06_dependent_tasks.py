from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from foundation_kaia.releasing.mddoc import ControlValue
api = BrainBox.Api("http://127.0.0.1:8090")

result_1_control_value = ControlValue.mddoc_define_control_value([6, 16])
result_2_control_value = ControlValue.mddoc_define_control_value(16)
result_3_control_value = ControlValue.mddoc_define_control_value([[0.0, {'index': 0}], [1.0, {'index': 1}], [2.0, {'index': 2}], [3.0, {'index': 3}], [4.0, {'index': 4}]])

if __name__ == '__main__':
    """
    ### Build a workflow from tasks

    The output of a task can serve as the input to another task:
    """
    task1 = HelloBrainBox.new_task().sum(2, 4)
    task2 = HelloBrainBox.new_task().sum(task1, 10)
    result = api.execute([task1, task2])

    """
    The result will be:
    """

    result_1_control_value.mddoc_validate_control_value(result)


    """
    In this case, `task1` will be executed before `task2`, and the output of
    `task1` will be used as an argument to `task2`.
    
    The same pipeline can be arranged in a more elegant way:
    
    """

    task = HelloBrainBox.new_task().sum(
        10,
        HelloBrainBox.new_task().sum(2,4)
    )

    result = api.execute(task)

    """
    The result will be:
    """

    result_2_control_value.mddoc_validate_control_value(result)

    """
    ### Collect the outputs of many tasks

    One particularly important use case of the dependent tasks is when
    several tasks are run, each associated with some __tags__ describing a task,
    and then the outputs of all tasks are collected together and returned as a single entity.

    `Collector` does just this. The simplest way to use it is via `Collector.TaskBuilder`:
    """
    from brainbox.deciders import Collector

    builder = Collector.TaskBuilder()
    for i in range(5):
        builder.append(task=HelloBrainBox.new_task().sum(0, i), tags=dict(index=i))
    pack = builder.to_collector_pack('to_array')
    result = [[r['result'], r['tags']] for r in api.execute(pack)]
    result_3_control_value.mddoc_validate_control_value(result)



