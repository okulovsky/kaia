from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from foundation_kaia.releasing.mddoc import ControlValue
api = BrainBox.Api("http://127.0.0.1:8090")

tokens_control_value = ControlValue.mddoc_define_control_value(b'{"token": "hello"}{"token": "world"}')
log_control_value = ControlValue.mddoc_define_control_value(['Step 0', 'Step 1', 'Step 2', 'Step 3'])
result_control_value = ControlValue.mddoc_define_control_value("RESULT")

if __name__ == '__main__':
    """
    ### Stream results from a decider

    Some deciders produce output incrementally — for example, a text-to-speech
    engine that generates audio token by token. BrainBox supports this via
    _streaming endpoints_, which use WebSockets internally.

    `HelloBrainBox.stream_voiceover` is a streaming endpoint: it accepts a
    list of text tokens and yields one audio chunk per token.
    BrainBox collects all chunks and stores them as a single file:
    """

    import json

    tokens = [dict(text='hello'), dict(text='world')]
    result = api.execute(HelloBrainBox.new_task().stream_voiceover(tokens))
    content = api.cache.read(result)

    """
    The result will be:
    """
    tokens_control_value.mddoc_validate_control_value(content)
    """
    The streaming is transparent from the caller's perspective:
    you call `stream_voiceover` just like any other endpoint, and BrainBox
    handles the WebSocket communication and aggregation internally.
    
    If you wish, however, to access the file __while__ it's been written,
    you may use `api.streaming_cache`. This will allow to start reading immediately after adding the task,
    and progress over the resulting stream as it arrives. 

    ### Run a long background process

    Some tasks, such as model training, run for a long time and produce
    intermediate progress reports. BrainBox supports this via the same
    streaming mechanism: the decider yields `BrainboxReportItem` objects
    with log messages and progress values, and BrainBox exposes them through
    the job status API.

    `HelloBrainBox.training` demonstrates this pattern:
    """

    import time

    training_id = api.add(HelloBrainBox.new_task().training(b'abcd'))

    while True:
        try:
            status = api.tasks.get_job_summary(training_id)
            if status.progress is not None and status.progress > 0:
                break
        except Exception:
            pass
        time.sleep(0.1)

    log = api.tasks.get_log(training_id)

    """
    The training task is submitted with `api.add`, which returns immediately
    with the task ID. Progress and log entries are available via
    `api.tasks.get_job_summary` (for progress) and `api.tasks.get_log` (for log lines).
    
    The `log` will be:
    
    """

    log_control_value.mddoc_validate_control_value(lambda: "Step 0" in log and len(log)>1)

    """
    Once the task completes, `api.join` returns the path to a `.jsonl` file
    containing all `BrainboxReportItem` entries. The final entry carries the
    actual result value in its `result` field.
    """

    import json

    result_file = api.join(training_id)
    lines = api.cache.read(result_file).decode('utf-8').split('\n')
    final_result = None
    for line in lines:
        if line.strip():
            js = json.loads(line)
            if js.get('result') is not None:
                final_result = js['result']

    """
    The final result will be:
    """
    result_control_value.mddoc_validate_control_value('RESULT')

