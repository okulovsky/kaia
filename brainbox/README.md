# Table of contents

* [Introduction](#introduction)
  * [Included deciders](#included-deciders)
    * [Text-to-speech](#text-to-speech)
    * [Speech-to-text and voice analysis](#speech-to-text-and-voice-analysis)
    * [LLM and text processing](#llm-and-text-processing)
    * [Image generation and processing](#image-generation-and-processing)
* [Installation](#installation)
  * [Docker](#docker)
  * [Python environment](#python-environment)
  * [BrainBox](#brainbox)
  * [Troubleshooting](#troubleshooting)
* [Python's API](#python's-api)
  * [Basic techniques](#basic-techniques)
    * [Create an API object](#create-an-api-object)
    * [Install the decider](#install-the-decider)
    * [Run a self-test](#run-a-self-test)
    * [Call an endpoint](#call-an-endpoint)
    * [Select a model via parameter](#select-a-model-via-parameter)
    * [Select a model as a method's argument](#select-a-model-as-a-method's-argument)
    * [Upload files required by deciders](#upload-files-required-by-deciders)
  * [Advanced techniques](#advanced-techniques)
    * [Models' management](#models'-management)
    * [Stream results from a decider](#stream-results-from-a-decider)
    * [Run a long background process](#run-a-long-background-process)
    * [Build a workflow from tasks](#build-a-workflow-from-tasks)
    * [Collect the outputs of many tasks](#collect-the-outputs-of-many-tasks)
* [Usage ways](#usage-ways)
  * [Direct decider's calls](#direct-decider's-calls)
  * [Non-python usage](#non-python-usage)
    * [HTTP direct access](#http-direct-access)
    * [HTTP access to the brainbox](#http-access-to-the-brainbox)
    * [Containerization](#containerization)

# Introduction

BrainBox provides easy HTTP access to a set of curated Docker containers
with AI-systems that process images, texts and sounds.
It comes with API endpoints to build the container, download basic models,
perform self-tests, as well as unified access to all the models and documentation.
The main use case is fast prototyping of small AI-driven products:
managing chats in messengers, self-hosted voice assistants,
media processing (translation, covering images), etc.
BrainBox can also serve as a bridge between your non-Python application, be it front- or backend,
and the pythonic world of AIs: the HTTP calls have the predictable format
and can be performed from any programming language.
For Python, the elegant and easy-to-use API is provided.

BrainBox is open-source and self-hosted, no external APIs are needed.
All the data are processed on your device.

The suggested use of BrainBox is your own home machine or the remote server accessible via VPN.
BrainBox doesn't have any security features, so the access control must be provided on the network, not application, level.
Ideally, this machine would have a decent GPU unit: many AI-systems do not require GPU,
but some (the most interesting ones, of course) are practically useless without it,
and few won't even run.

## Included deciders

There are many! Once you install BrainBox, you will have all these AIs privately and free of charge on your machine,
accessible via user-friendly Python API, or by simple HTTP requests.

### Text-to-speech

Best choice:
* [Piper](https://github.com/rhasspy/piper) - fast and resource-efficient text-to-speech.
Lots of languages are supported.
* [CosyVoice](https://github.com/Zyphra/Zonos) - ultimate solution for artistic, multilingual voice-cloning.
Perfect results in terms of quality and stability.
* PiperTraining: a container to train models for Piper.

### Speech-to-text and voice analysis

* [Whisper](https://github.com/WhisperSpeech/WhisperSpeech) is a de-facto standard.
* [Kaldi](https://kaldi-asr.org/), which we use via its implementation in [Rhasspy](https://rhasspy.readthedocs.io/en/latest/),
  provides much faster and accurate result _over the closed grammar and vocabulary_.
  It is not really a general solution for STT, but is perfect for home assistants.
* [Resemblyzer](https://github.com/resemble-ai/Resemblyzer) does speaker identification.
* [Vosk](https://alphacephei.com/vosk/) - can be faster than Whisper,
also the results have more direct connection to the audio, e.g. each word is located to timestamps.

### LLM and text processing

* [Ollama](https://ollama.com/), a de-facto standard for LLM management, is supported.
* [EspeakPhonemizer](https://pypi.org/project/espeak-phonemizer/) converts text to phonemes for many languages.
Mainly here because of how troublesome it is to install it on Windows.

### Image generation and processing
* [YOLO](https://docs.ultralytics.com/) is used for fast object detection with neural netowrks.
* [WD14Tagger](https://github.com/corkborg/wd14-tagger-standalone) describes the images with the tags.
Also available in ComfyUI, but has some additional perks.
* VideoToImages converts video to a series on images, allowing to select most sharp frame and to skip similar frames.

# Installation

## Docker

You need [Docker](https://docs.docker.com/engine/install/) installed in your system,
and the access granted to the current user to run `docker` from command line without elevated privileges.
The command

```commandline
docker run hello-world
```

should work successfully and produce the text starting with "Hello from Docker!"

## Python environment

[Anaconda](https://www.anaconda.com/download/success) is recommended to manage Python's
environments. Create an environment for e.g. Python 3.12 (BrainBox is tested with 3.10-3.13 Python versions):

```commandline
conda create --name brainbox python==3.11
```

Then, activate the environment

```commandline
conda activate brainbox
```

## BrainBox

Install the brainbox

```commandline
pip install kaia-brainbox
```

Run the brainbox

```commandline
python -m brainbox.run --data-folder <where_all_files_will_be_stored>
```

You should see something like:
```
Starting server on http://127.0.0.1:8090
```

If you see:
```
ERROR:    [Errno 98] error while attempting to bind on address ('0.0.0.0', 8090): [errno 98] address already in use
```
consult the Troubleshooting section.

Run the build-in test. It will make sure that all the functions, mentioned in this README, work correctly

```python
python -m brainbox.run_test
```

If you see `ALL GOOD` in the end, it means BrainBox is installed and ready.

## Troubleshooting

If the port is busy:
* Maybe the port `8090` assigned to other application in your system. In this case, use `--port` argument to both
  `brainbox.run` and `brainbox.run_test` commands.
* Maybe you try to run the second instance of the BrainBox on the same port. Don't do it.
* Maybe you were running BrainBox before and shut it down incorrectly.
  In this case, check your processes and kill those from `python`.
  Or simply restart the machine.





# Python's API

This is the simplest way to access the BrainBox functionality.
To use it, install BrainBox to your project with `pip install kaia-brainbox`

To execute the following code, you need to run BrainBox and keep it running.

Note, that the code below is also part of the tests and is located at `/doc`.
In this documentation, regions from this test are copy-pasted,
along with asserts for better understanding of returned values,
so `test_case` represents a `unittest` TestCase instance.

## Basic techniques

These are the operations you use for all the deciders all the time you work with BrainBox.

### Create an API object

```python
from brainbox import BrainBox

api = BrainBox.Api("http://127.0.0.1:8090")
api.wait_for_connection(1)
```

This will create an API object. `wait_for_connection` will try to connect to the endpoint
for 1 second, and raises if unsuccessful.

### Install the decider

We have a `HelloBrainBox` decider, that doesn't do anything useful,
but accumulates all the features BrainBox has for deciders.
Let's install the decider:

```python
from brainbox.deciders import HelloBrainBox

api.controllers.install.execute(HelloBrainBox)
```

Note that the container is not pulled, but built on your machine,
and this is also the case for other deciders.
This is resource-intensive, in terms of bandwidth and time,
but allows you to modify the containers quickly
if you require some model's functionality that wasn't implemented.
Also it allows BrainBox to work completely independently,
with the source code only, without reliance on external
docker repositories; and finally, it's much easier to check what
these containers are doing.

During installation, BrainBox also downloads the models listed in
`HelloBrainBox.Settings.models_to_install`. These are the models the
decider needs in order for its self-test to run successfully.

Returned `report` can largely be ignored, it's only needed for
GUI purposes.

### Run a self-test

The self-tests for the deciders run the most important endpoints,
and ensure their correct work.
Also, they provide a report where you can see the inputs and outputs
for the endpoint, so it is documentation of some sort.
This report can be viewed as an HTML page.

This will run a self-test and opens the result in the web-browser.

```python
import requests, webbrowser, tempfile
from pathlib import Path

key = api.controllers.self_test.start(HelloBrainBox)
api.controllers.self_test.join(key)
report = api.controllers.self_test.html_report(key)

test_case_test_path = Path(tempfile.gettempdir()) / 'test_report.html'
with open(test_case_test_path, 'w', encoding='utf-8') as file:
    file.write(report)
```

and then:

```python
webbrowser.open('file://'+str(test_case_test_path))
```

Self-test reports provide some understanding of the endpoints.
I also recommend reading the controller's page in the BrainBox UI. 
Reading the self-tests code also helps a lot: all the endpoints are called
in the same way you will call them from your Python code.

Self-tests, building containers and other container-related things
are performed by `Controller` classes. They are usually located
within entry-point-objects, e.g. `HelloBrainBox` is an entry-point-object,
and HelloBrainBox.Controller is a controller type.

### Call an endpoint

This will execute the method `HelloBrainBox::sum` on the server side.

```python
from brainbox.deciders import HelloBrainBox

result = api.execute(HelloBrainBox.new_task().sum(2, 4))
```

The result will be:

```
6
```

The BrainBox will run the container for the HelloBrainBox decider.
This container has a web-server inside, and `HelloBrainBox.sum`
connects to this web-server and performs the required operation.
The result (in this case, a number) is then returned to the caller.

BrainBox is smart and tries to minimize the containers' runs.
If several tasks for the same decider have arrived,
this decider will be set up, and then all these tasks will be executed
before the tasks for other deciders.

### Select a model via parameter

For a very few deciders, the model must be selected before running the container,
and this is done with container parameter. Ollama is one of such deciders,
so the call would be:

```python
result = api.execute(Ollama.new_task(parameter='mistral-small').question("What's the recipe for borsh?"))
```

Also, new_task can specify:
* `id`, in case you want the job to have a non-random ID
* `info`: arbitrary JSON assotiate with a task, helpful when you want to associate some tags with a task and retrieve them later

### Select a model as a method's argument

Most of the deciders do not use a container parameter to select a model
(and also, using container parameter is not the best practice for this and is discouraged in the newer deciders).
Instead, the model is passed directly as a method argument.
This is more flexible: multiple models can be used within the same
container session, and the model is loaded on demand.

`HelloBrainBox.voiceover` accepts an optional `model` argument.
The available models are listed in `HelloBrainBox.Settings.models_to_install`
and are downloaded automatically during installation.

```python
import json

result = api.execute(HelloBrainBox.new_task().voiceover('hello', HelloBrainBox.Models.google))
file = api.cache.read(result)
content = json.loads(file)
```

Since this endpoint plays the role of voiceover, it does not return the content as-is 
(otherwise the BrainBox database would be very soon overflown by gygabytes of the images and sounds).
Instead, the content is placed in a file, and the name of this file is returned. 
The content is then retrieved via `api.cache`. 

The `HelloBrainBox.Models` enum lists the pre-configured models.
You can also pass the model name as a plain string.

The result will be:

```
{'model': '[LOADED] /resources/models/google', 'text': 'hello'}
```

Since the model was already loaded by the previous call, you may now omit the argument:

```python
result = api.execute(HelloBrainBox.new_task().voiceover('hey'))
file = api.cache.read(result)
content = json.loads(file)
```

The content will be:

```
{'model': '[LOADED] /resources/models/google', 'text': 'hey'}
```

You can also switch the model manually:

```python
api.execute(HelloBrainBox.new_task().load_model(HelloBrainBox.Models.facebook))
result = api.execute(HelloBrainBox.new_task().voiceover('hola'))
file = api.cache.read(result)
content = json.loads(file)
```

That will produce:

```
{'model': '[LOADED] /resources/models/facebook', 'text': 'hola'}
```

However, this is not recommended. 
The best way is to always specify the model in the task itself to avoid interdependencies 
between tasks runs. 
The model loading setup that is used by HelloBrainBox is shared between many other deciders
via the interface `IModelLoadingSupport` and `SingleModelStorage`, defined in foundation_kaia.brainbox_utils.

### Upload files required by deciders

Some deciders, especially speech-to-text or audio analysis,
use files as inputs. You may feed bytes directly in the call:

```python
data = b'12112'
result = api.execute(HelloBrainBox.new_task().voice_embedding(data))
```

This decider counts the occurrences of bytes from `0` to `9` value
and returns a list of 10 counts — one per possible byte value, so the result is:

```
[0.0, 3.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
```

However, passing large binary data inline has the potential to overload the
database, and should be avoided for large files.

To avoid this, you may choose to upload the file to the BrainBox
cache folder instead:

```python
from brainbox import File

api.cache.upload('test', b'12112')
result = api.execute(HelloBrainBox.new_task().voice_embedding('test'))
```

The result will remain the same:

```
[0.0, 3.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
```

By uploading the file to the cache folder first, you decouple the data
transfer from the task execution. The decider receives only the filename
and reads the file from the shared cache.

This solution scales to remote BrainBox instances as well,
since the upload is handled separately from the task.

## Advanced techniques

### Models' management

Many deciders support multiple models that need to be downloaded before use.
The models a decider downloads during installation are declared in
`Settings.models_to_install`:

```python
models = HelloBrainBox.Settings.models_to_install
```

The `models` variable is:

```
{'facebook': HelloBrainBoxModelSpec(url='https://facebook.com'),
 'google': HelloBrainBoxModelSpec(url='https://google.com')}
```

These models are downloaded automatically when the decider is installed.
You can list them using the resources API:

```python
resources = api.resources(HelloBrainBox).list('models', glob=True)
```

The result should be:

```
['facebook', 'google']
```

The actual result may be different if you previously installed other models.

Each decider has its own _resource folder_ on the host file system,
mounted into the container. Model files live in the `models/` subfolder
of that resource folder.

If you need to download an additional model that was not included in
`models_to_install`, you can trigger the download via BrainBox:

```python
api.execute(
    HelloBrainBox.new_task().download_model(
        'microsoft',
        HelloBrainBox.ModelSpec('http://microsoft.com')
    )
)

resources = api.resources(HelloBrainBox).list('models', glob=True)
```

The result should be:

```
['facebook', 'google', 'microsoft']
```

The `download_model` endpoint is provided by `IModelInstallingSupport`.
After the download, the model is registered in the decider's
`installation.yaml` and available for use in subsequent calls.

### Stream results from a decider

Some deciders produce output incrementally — for example, a text-to-speech
engine that generates audio token by token. BrainBox supports this via
_streaming endpoints_, which use WebSockets internally.

`HelloBrainBox.stream_voiceover` is a streaming endpoint: it accepts a
list of text tokens and yields one audio chunk per token.
BrainBox collects all chunks and stores them as a single file:

```python
import json

tokens = [dict(text='hello'), dict(text='world')]
result = api.execute(HelloBrainBox.new_task().stream_voiceover(tokens))
content = api.cache.read(result)
```

The result will be:

```
b'{"token": "hello"}{"token": "world"}'
```

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

```python
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
```

The training task is submitted with `api.add`, which returns immediately
with the task ID. Progress and log entries are available via
`api.tasks.get_job_summary` (for progress) and `api.tasks.get_log` (for log lines).

The `log` will be:

```
['Step 0', 'Step 1', 'Step 2', 'Step 3']
```

Once the task completes, `api.join` returns the path to a `.jsonl` file
containing all `BrainboxReportItem` entries. The final entry carries the
actual result value in its `result` field.

```python
import json

result_file = api.join(training_id)
lines = api.cache.read(result_file).decode('utf-8').split('\n')
final_result = None
for line in lines:
    if line.strip():
        js = json.loads(line)
        if js.get('result') is not None:
            final_result = js['result']
```

The final result will be:

```
'RESULT'
```

### Build a workflow from tasks

The output of a task can serve as the input to another task:

```python
task1 = HelloBrainBox.new_task().sum(2, 4)
task2 = HelloBrainBox.new_task().sum(task1, 10)
result = api.execute([task1, task2])
```

The result will be:

```
[6, 16]
```

In this case, `task1` will be executed before `task2`, and the output of
`task1` will be used as an argument to `task2`.

The same pipeline can be arranged in a more elegant way:

```python
task = HelloBrainBox.new_task().sum(
    10,
    HelloBrainBox.new_task().sum(2,4)
)

result = api.execute(task)
```

The result will be:

```
16
```

### Collect the outputs of many tasks

One particularly important use case of the dependent tasks is when
several tasks are run, each associated with some __tags__ describing a task,
and then the outputs of all tasks are collected together and returned as a single entity.

`Collector` does just this. The simplest way to use it is via `Collector.TaskBuilder`:

```python
from brainbox.deciders import Collector

builder = Collector.TaskBuilder()
for i in range(5):
    builder.append(task=HelloBrainBox.new_task().sum(0, i), tags=dict(index=i))
pack = builder.to_collector_pack('to_array')
result = [[r['result'], r['tags']] for r in api.execute(pack)]
```

```
[[0.0, {'index': 0}],
 [1.0, {'index': 1}],
 [2.0, {'index': 2}],
 [3.0, {'index': 3}],
 [4.0, {'index': 4}]]
```

# Usage ways

## Direct decider's calls

Once the decider's instance is spawned, it can be accessed directly without any BrainBox at all.
So it is possible for instance to build the container on your local machine, 
deliver it to your remote machine via `docker pull/push`, run there and communicate directly to it,
avoiding BrainBox queuing and caching.

We will run the container with api:

```python
api.controllers.run(HelloBrainBox)
hello_api = HelloBrainBox.Api(f"http://127.0.0.1:{HelloBrainBox.Settings().connection.port}")
hello_api.wait_for_connection()

result = hello_api.sum(3,4)
```

The result will be:

```
7
```

Since BrainBox is not involved in the calling process, mids the following limitations:

* If an argument is a file and you use a string as a file name, it will not be taken from the BrainBox cache folder.
Instead, this string will be interpreted as a full path to the file on the machine the server is running.
You need to ensure the file is there yourself, as there is not universal cache and endpoints to work with this cache.
However, you can always send file as the raw bytes: we avoid it when working via BrainBox so the database is not overloaded,
but with the direct access, there is no database and no limitation.
* If a returning value of an endpoint is a file, it won't be cached in the BrainBox folder. Instead, its binary content 
will be given over HTTP protocol.

## Non-python usage

The important feature of BrainBox is that you don't need to use PythonAPI or Python in general to work with it.
You may start the server and then access all the functionality by sending the HTTP requests to it. 

The BrainBox external API, as well as the API of each of the deciders's servers,
is written with `foundation_kaia.marshalling` which allows you to automatically build the server and the API
from the Python's annotations, provides a clear format of HTTP requests and replies, 
and also generates its own documentation. So there is 1-to-1 mapping from the functions arguments to the 
content of the HTTP request and vice-versa. Also, there is automatically generated documentation
for the BrainBoxApi and all of the deciders' API. 

### HTTP direct access

The direct access is straightforward. 
First, you can go to the `http://127.0.0.1:20000/doc/html` and read the documentation to the decider's endpoints.
You can also request this information in JSON format:

```python
import requests
from pprint import pprint

response = requests.get("http://127.0.0.1:20000/doc/json")
response.raise_for_status()
pprint(response.json())
```

Then, call the decider:

```python
response = requests.post(
    "http://127.0.0.1:20000/hello-brain-box/sum",
    json={
        "a": 3,
        "b": 4
    }
)
response.raise_for_status()
```

`response.json` will contain: 

```
7
```

### HTTP access to the brainbox

You can read documentation to the brainbox api at the same page `/doc/html`.

All the controllers operations such as installing, starting, stopping the controller are supported in the API.
However, some of these operations are needed only once (like installing), and some others are managed by
BrainBox internally (such as starting the containers). Therefore, it makes more sense to use BrainBox GUI for them.    
So we will cover only the API to create the tasks in this section.

To add the task, you need to use `/tasks-service/base-add` with the list of tasks you want to create:

```python
from uuid import uuid4

id = str(uuid4())
response = requests.post("http://127.0.0.1:8090/tasks-service/base-add", json={
    "jobs":
        [
            {
                "id": id,
                "decider": "HelloBrainBox",
                "method": "sum",
                "arguments": {
                    "a": 4,
                    "b": 5
                },
            },
            {
                "decider": "HelloBrainBox",
                "method": "sum",
                "arguments": {
                    "a": 10
                },
                "dependencies": {
                    "b": id
                }
            }
        ]
})
response.raise_for_status()
```

We add two tasks where the second one depends on the first one. This is the correct ordering:
the root comes last. This is because of the consistency checks: if the tasks depends on something,
this something needs to be already in the queue.

For the first task, we specify the `id` as we need to reuse it in the `dependencies` of the second task.
For the second task, we may omit ID, it will be assigned automatically.   

`base-add` endpoint returns the list of its. You can then wait for them to finish and retrieve the result:     

```python
ids = response.json()
response = requests.post(
    "http://127.0.0.1:8090/tasks-service/base-join",
    json = {
        "ids": ids
    }
)
response.raise_for_status()
```

`response.json` will be: 

```
[9.0, 19.0]
```

Now, let's explore how to work with the files. The files are managed by `/cache` endpoints. 

Let's upload the source file: 

```python
id = str(uuid4())
response = requests.post(
    f"http://127.0.0.1:8090/cache/upload/{id}",
    data = b'Hello, world!'
)
response.raise_for_status()
```

Then, we will run the decider:

```python
response = requests.post(
    "http://127.0.0.1:8090/tasks-service/base-add",
    json = {
        "jobs" : [{
            "decider": "HelloBrainBox",
            "method": "voice_clone",
            "arguments": {
                "original": id,
            }
        }]
    }
)
ids = response.json()
response = requests.post(
    "http://127.0.0.1:8090/tasks-service/base-join",
    json = {"ids": ids}
)
response.raise_for_status()
result = response.json()[0]
```

`result` will contain the file name, which needs to be retrieved from the cache:

```python
response = requests.get(
    f"http://127.0.0.1:8090/cache/open/{result}",
)
response.raise_for_status()
```

Since `HelloBrainBox` is a demo server, this file is actually a JSON file disguised as a binary file. 

```python
import json

json_result = json.loads(response.text)
```

`json_result` is:

```
{'model': '[LOADED] /resources/models/google', 'text': 'Hello, world!'}
```

### Containerization

BrainBox can be used from within the container. Since will be a container that manages other containers,
the following must be observed:
* `docker` needs to be installed inside the BrainBox image. 
* `/var/run/docker.sock` must be mounted inside the container. It also needs to be writable on the host machine.
* BrainBox will mount the folders to the containers it creates. 
Since this mounting is actually going to happen on the host machine, the name of the BrainBox folder must be the same 
as at the host machine. So it will look like this:
`docker run --mount type=bind,source={BBPATH},target={BBPATH} brainbox --data-folder BBPATH
* BrainBox will communicate with the containers it creates over network, so `--network host` is required.
* GPU needs to be shared with this container

If you develop BrainBox in the repository and want to containerize the repo's current state, 
you may use `brainbox.framework.container` module. 