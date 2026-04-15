from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase

def model_management(test_case: TestCase, api: BrainBox.Api):
    """
    ## Advanced techniques

    ### Manage models

    Many deciders support multiple models that need to be downloaded before use.
    The models a decider downloads during installation are declared in
    `Settings.models_to_install`:

    ```python
    HelloBrainBox.Settings.models_to_install
    # {'google': HelloBrainBoxModelSpec(url='http://google.com'),
    #  'duckduckgo': HelloBrainBoxModelSpec(url='http://duckduckgo.com')}
    ```

    These models are downloaded automatically when the decider is installed.
    You can list them using the resources API:
    """

    resources = api.resources(HelloBrainBox).list('models', glob=True)
    test_case.assertIn('google', resources)
    test_case.assertIn('duckduckgo', resources)

    """
    Each decider has its own _resource folder_ on the host file system,
    mounted into the container. Model files live in the `models/` subfolder
    of that resource folder.

    If you need to download an additional model that was not included in
    `models_to_install`, you can trigger the download via BrainBox:
    """

    from brainbox.deciders.utils.hello_brainbox.app.model import HelloBrainBoxModelSpec

    api.execute(
        HelloBrainBox.new_task().download_model(
            'my_model',
            HelloBrainBoxModelSpec('http://google.com')
        )
    )
    resources = api.resources(HelloBrainBox).list('models', glob=True)
    test_case.assertIn('my_model', resources)

    """
    The `download_model` endpoint is provided by `IModelInstallingSupport`.
    After the download, the model is registered in the decider's
    `installation.yaml` and available for use in subsequent calls.
    """

def streaming(test_case: TestCase, api: BrainBox.Api):
    """
    ### Stream results from a decider

    Some deciders produce output incrementally — for example, a text-to-speech
    engine that generates audio token by token. BrainBox supports this via
    _streaming endpoints_, which use WebSockets internally.

    `HelloBrainBox::stream_voiceover` is a streaming endpoint: it accepts a
    list of text tokens and yields one audio chunk per token.
    BrainBox collects all chunks and stores them as a single file:
    """

    import json

    tokens = [dict(text='hello'), dict(text='world')]
    result = api.execute(HelloBrainBox.new_task().stream_voiceover(tokens))
    file = api.cache.read_file(result)
    test_case.assertEqual(
        b'{"token": "hello"}{"token": "world"}',
        file.content
    )

    """
    The streaming is transparent from the caller's perspective:
    you call `stream_voiceover` just like any other endpoint, and BrainBox
    handles the WebSocket communication and aggregation internally.

    ### Run a long background process

    Some tasks, such as model training, run for a long time and produce
    intermediate progress reports. BrainBox supports this via the same
    streaming mechanism: the decider yields `BrainboxReportItem` objects
    with log messages and progress values, and BrainBox exposes them through
    the job status API.

    `HelloBrainBox::training` demonstrates this pattern:
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
    test_case.assertIsNotNone(log)
    test_case.assertGreater(len(log), 0)

    import json

    result_file = api.join(training_id)
    lines = api.cache.read_file(result_file).string_content.split('\n')
    final_result = None
    for line in lines:
        if line.strip():
            js = json.loads(line)
            if js.get('result') is not None:
                final_result = js['result']
    test_case.assertEqual('RESULT', final_result)

    """
    The training task is submitted with `api.add`, which returns immediately
    with the task ID. Progress and log entries are available via
    `api.tasks.get_job_summary` (for progress) and `api.tasks.get_log` (for log lines).
    Once the task completes, `api.join` returns the path to a `.jsonl` file
    containing all `BrainboxReportItem` entries. The final entry carries the
    actual result value in its `result` field.
    """
