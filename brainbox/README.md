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
    * [Call an enpoint with a parameter](#call-an-enpoint-with-a-parameter)
    * [Download files, produced by deciders](#download-files,-produced-by-deciders)
    * [Upload files, required by deciders](#upload-files,-required-by-deciders)
  * [Advanced techniques](#advanced-techniques)
    * [Browse the resources](#browse-the-resources)
    * [Download a custom model](#download-a-custom-model)
    * [Build a workflow from tasks](#build-a-workflow-from-tasks)
    * [Collect the outputs of many tasks](#collect-the-outputs-of-many-tasks)
    * [Collect the files from many tasks](#collect-the-files-from-many-tasks)
* [Use it without Python](#use-it-without-python)
  * [Manage the controllers](#manage-the-controllers)
  * [Run the tasks](#run-the-tasks)

# Introduction

BrainBox provides easy HTTP access to a set of curated Docker containers 
with AI-systems processing images, texts and sounds.
It comes with API endpoints to build the container and download basic models, 
self-tests and documentation, as well as unified access to all the models.
The main use case is fast prototyping of small AI-driven products: 
managing chats in messengers, self-hosted voice assistants, 
media processing (translation, covering images), etc.
BrainBox is open-source and self-hosted, so no external APIs are needed.

BrainBox is not a production-ready solution. **Do not use it in production environment**,
since it doesn't have any security features, isn't really compatible with high and even 
moderate load, and at the same time may have a big impact on the system's resources. 
The suggested use of BrainBox is your own home machine, 
where the security is provided on the network, not application, level.
Ideally, this machine would have a decent GPU unit: many AI-systems do not require GPU,
but some (the most interesting ones, of course) are practically useless without it,
and few won't even run.

## Included deciders

There are many! Once you install BrainBox, you will have all these AIs privately and free of charge on your machine, 
accessible via user-friendly Python API, or by simple HTTP requests.

At some point, BrainBox will have a comprehensive documentation for each of them, but we're not there yet.
So here is a short description.

### Text-to-speech

* [OpenTTS](https://github.com/synesthesiam/opentts) provides a decent baseline for English language with VITS model, other languages are supproted as well.
* [CoquiTTS](https://github.com/coqui-ai/TTS) is a framework supporting many different models.
  That includes VITS as well as YourTTS, and, of course, their own XTTS, that can do a good voice cloning.
* [TortoiseTTS](https://github.com/neonbjb/tortoise-tts) is, in my opinion, still the best in terms of quality. 
  It is very slow, but not as slow as it used to be. 

### Speech-to-text and voice analysis
 
* [Whisper](https://github.com/WhisperSpeech/WhisperSpeech) is a de-facto standard.
* [Kaldi](https://kaldi-asr.org/), which we use via its implementation in [Rhasspy](https://rhasspy.readthedocs.io/en/latest/),
  provides much faster and accurate result _over the closed grammar and vocabulary_. 
  It is not really a general solution for STT, but is perfect for home assistants.
* [Resemblyzer](https://github.com/resemble-ai/Resemblyzer) does speaker identification.

### LLM and text processing 

* [Ollama](https://ollama.com/), a de-facto standard for LLM management, is supported.
* [EspeakPhonemizer](https://pypi.org/project/espeak-phonemizer/) converts text to phonemes for many languages. 
Mainly here because of how troublesome it is to install it on Windows.

### Image generation and processing
* [ComfyUI](https://github.com/comfyanonymous/ComfyUI), a standard for image generation, is supported
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
environments. Create an environment for e.g. Python 3.11 (BrainBox is tested with 3.10-3.13 Python versions):

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
 * Serving Flask app 'RPC_BrainBoxService'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8090
```

Please check the Troubleshooting session if instead you see something like this:
```
 * Serving Flask app 'RPC_BrainBoxService'
 * Debug mode: off
Address already in use
Port 8090 is in use by another program. Either identify and stop that program, or start the server with a different port.
```

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
To use it, simply install BrainBox to your project with `pip install brainbox`

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

api = BrainBox.Api("127.0.0.1:8090")
api.wait(1)
```

This will create an API object. `wait` will try to connect to the endpoint
for 1 second, and raises if unsuccessful.

### Install the decider

We have a `HelloBrainBox` decider, that doesn't do anything useful,
but accumulates all the features BrainBox has for deciders.
Let's install the decider:

```python

from brainbox.deciders import HelloBrainBox

report = api.controller_api.install(HelloBrainBox)
test_case.assertIsNotNone(report)

```

Note that the container is not pulled, but build on your machine, 
and this is also the case for other deciders. 
This is resource-intensive, in terms of bandwidth and time,
but allows you to modify the containers quickly 
if you require some model's functionality that wasn't implemented.
Also it allows BrainBox to work completely independently,
with the source code only, without reliance to the external 
docker repositories; and finally, it's much easier to check what 
these containers are doing.

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

api.controller_api.self_test(HelloBrainBox)
self_test_report = requests.get(f'http://{api.address}/html/controllers/self_test_report/HelloBrainBox').text
test_case.assertIsInstance(self_test_report, str)

test_case_test_path = Path(tempfile.gettempdir()) / 'test_report.html'
with open(test_case_test_path, 'w', encoding='utf-8') as file:
    file.write(self_test_report)

```

and then:

```python
webbrowser.open('file://'+str(test_case_test_path))
```

While self-test reports provide some understanding of the endpoints,
I recommend reading the self-tests code: all the endpoints are called 
in the same way you will call them from your Python code.
Self-tests, building containers and other container-related things
are performed by `Controller` classes. They are usually located
within deciders classes, e.g. `HelloBrainBox.Controller`

### Call an endpoint

This will execute the method HelloBrainBox::json on the server side.

```python

result = api.execute(BrainBox.Task.call(HelloBrainBox).json("Hello"))
test_case.assertDictEqual(
    {
        'argument': 'Hello',
        'model': 'no_parameter',
        'setting': 'default_setting'
    },
    result
)

```

The BrainBox will run the container for the HelloBrainBox decider.
This container has a web-server inside, and HelloBrainBox::json 
connects to this web-server and performs the required operation.
The result (in this case, `dict`) is then returned to the caller.
As you see, `argument` equals to the argument the code provides.

BrainBox is smart and tries to minimize the containers' runs.
If several tasks for same decider have arrived,
this decider will be set up, and then all these tasks will be executed
before the tasks for other deciders.

### Call an enpoint with a parameter

Few deciders have parameters: a string argument that will be fed to the container
on the start, and may modify its behaviour. It's sometimes required
when you don't build container from scratch, but use a ready container,
which requires you to load the model on the startup, and in this case,
`parameter` is this model's name.

To pass the parameter, simply add it to `call` function:

```python

result = api.execute(BrainBox.Task.call(HelloBrainBox, "parameter").json("Hello"))
test_case.assertDictEqual(
    {
        'argument': 'Hello',
        'model': 'parameter',
        'setting': 'default_setting'
    },
    result
)

```

As you can see, the `model` field is now set to `parameter`. 

Most of the deciders do not have the parameter and load models dynamically, so normally you write
`BrainBoxTask.call(DeciderClass).method(...)`

Please ignore the `setting` field. 
There is a possibility to adjust settings to the controllers,
such as the port the internal web-server will be assigned for,
or the list of models the controllers need to download,
but so far there was never a necessity to adjust them manually.
They are only used with the default values.

### Download files, produced by deciders

Many BrainBox deciders return files with generated images or sounds.
In order not to overload the BrainBox database with all these
gigabytes, the files are stored in the cache folder,
and only files' names are returned.

```python

filename = api.execute(BrainBox.Task.call(HelloBrainBox).file("Hello, file!"))
test_case.assertIsInstance(filename, str)

```

You may open this file with `api.open_file` method, which returns `File` 
instance, reading the content of the file on the fly. 

```python

from brainbox import File
import json

file = api.open_file(filename)
test_case.assertIsInstance(file, File)
test_case.assertDictEqual(
    {
        'argument': 'Hello, file!',
        'model': 'no_parameter',
        'setting': 'default_setting'
    },
    json.loads(file.content)
)

```

If you don't want to open the file, only download it on the disk:

```python
from pathlib import Path

path = api.download(filename)
test_case.assertIsInstance(path, Path)
with open(path, 'r') as stream:
    test_case.assertDictEqual(
        {
            'argument': 'Hello, file!',
            'model': 'no_parameter',
            'setting': 'default_setting'
        },
        json.load(stream)
    )

```

which simply downloads the file on the disk to the given location
(by default, in the API's cache folder), and returns the full path to file.
You may specify the location and the flag to redownload the file even
if it was already downloaded.

### Upload files, required by deciders

Some deciders, especially speech-to-text or image analysis, 
use files as inputs. You may feed them directly in the call:

```python
from brainbox import File

file = File('hello.txt', "Hello, world!")
test_case.assertEqual(file.name, 'hello.txt')
test_case.assertEqual(file.content, b'Hello, world!')

length = api.execute(BrainBox.Task.call(HelloBrainBox).file_length(file))
test_case.assertEqual(length, 13)

```

However, that has the potential to overload the database as well, 
and should be avoided.

If you run BrainBox server at the machine you're running `api`, 
you may pass the path of the file:

```python
import tempfile
from pathlib import Path

path = file.write(tempfile.gettempdir())
test_case.assertIsInstance(path, Path)

length = api.execute(BrainBox.Task.call(HelloBrainBox).file_length(path))
test_case.assertEqual(length, 13)
```

This solution is dirty as it won't work with a remote BrainBox, 
and would force you to rewrite your codebase in case of such change.

To avoid this, you may choose to upload the file to the BrainBox
cache folder instead:

```python

api.upload(file.name, file)
length = api.execute(BrainBox.Task.call(HelloBrainBox).file_length(file.name))
test_case.assertEqual(length, 13)

```

Sometimes, files are required to have specific names, or some
recoding. In these cases, deciders usually have static methods
that incapsulate these procedures in Prerequisites:

```python
upload_prerequisite = HelloBrainBox.file_upload(file)
upload_prerequisite.execute(api)
length = api.execute(BrainBox.Task.call(HelloBrainBox).file_length(file.name))
test_case.assertEqual(length, 13)

```

## Advanced techniques

### Browse the resources

Many deciders have _resources_: files, typically model files, that are passed to the containers and used for inference.
It is impractical to store them inside containers, and so BrainBox stores them in the host's file system:
each decider has its own resource folder, which is mounted to the container.

Aside from models, the training data may be stored in resources instead of file cache, as training data
are easier to organize with folder structure and predictable filenames.

This endpoint demonstrates that the server indeed has an access to the resources:
HelloBrainBox reads them and returns the dictionary of keys set to filenames,
and values set to file content.
These resources are created by HelloBrainBox controller as a part of installation procedure.

```python
resources = api.execute(BrainBox.Task.call(HelloBrainBox).resources())
test_case.assertDictEqual(
    {'nested/resource': 'HelloBrainBox nested resource', 'resource': 'HelloBrainBox resource'},
    resources
)

```

However, a uniform access to all the resources is provided by API, e.g. to list all the resources:

```python

resources = api.controller_api.list_resources(HelloBrainBox, '/')
test_case.assertListEqual(
    ['resource', 'nested/resource'],
    resources
)

```

### Download a custom model

Many deciders can run with different models, and these models need to be downloaded.
All the deciders load some models at the installation time to allow self-test to run.
However, more models are usually needed.

Sometimes the containers are able to download these models themselves,
but often enough the models need to be downloaded separately.

This action can be triggered via `api`:

```python

api.controller_api.download_models(HelloBrainBox, [HelloBrainBox.Model('google', 'http://www.google.com')])
resources = api.controller_api.list_resources(HelloBrainBox, '/models')
test_case.assertListEqual(['models/google'], resources)

```

### Build a workflow from tasks

The output of the tasks can serve as an input to other tasks:

```python
task1 = BrainBox.Task.call(HelloBrainBox).json("Hello")
task2 = BrainBox.Task.call(HelloBrainBox).json(task1)
result = api.execute([task1, task2])
test_case.assertDictEqual(result[0], result[1]['argument'])

```

In this case, the `task1` will be executed before `task2` and the output of `task1` will be used
as an argument for `task2` method.

### Collect the outputs of many tasks

One particularly important use case of the dependent tasks is when
several tasks are run, each associated with some __tags__ describing a task,
and then the outputs of all tasks are collected together and returned as a single entity.

`Collector` does just this. Declaring collector tasks in a raw form is very cumbersome,
 and we actually use helpers to do this,
 however, it helps to see what's going on under the hood.

```python
from brainbox.deciders import Collector
from brainbox import BrainBoxCombinedTask

id1 = BrainBox.Task.safe_id()
id2 = BrainBox.Task.safe_id()
task1 = BrainBox.Task.call(HelloBrainBox).json(0).to_task(id=id1)
task2 = BrainBox.Task.call(HelloBrainBox).json(1).to_task(id=id2)
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

```

Method `BrainBox.Task.safe_id` creates uuid4 and converts it in python literal so it can be used in **kwargs. 

We can shorten this significantly with `Collector.TaskBuilder`:

```python

builder = Collector.TaskBuilder()
for i in range(10):
    builder.append(task=BrainBox.Task.call(HelloBrainBox).json(i), tags=dict(index=i))
pack = builder.to_collector_pack('to_array')
array = api.execute(pack)
for item in array:
    test_case.assertIsNone(item['error'])
    test_case.assertEqual(item['tags']['index'], item['result']['argument'])

```

### Collect the files from many tasks

One problem remains: if deciders return files, these files won't be collected. 
To solve it, MediaLibrary structure is used. Essentially it's a zip-file
that contains all the outputs as well as tags. 

```python
from brainbox import MediaLibrary
from brainbox.deciders import Collector
import json

builder = Collector.TaskBuilder()
for i in range(10):
    builder.append(task=BrainBox.Task.call(HelloBrainBox).file(i), tags=dict(index=i))
pack = builder.to_collector_pack('to_media_library')
path = api.download(api.execute(pack))
ml = MediaLibrary.read(path)
for record in ml.records:
    content = record.get_content()
    tags = record.tags
    test_case.assertEqual(tags['index'], json.loads(content)['argument'])

```

# Use it without Python

All the BrainBox functionality is accessible without Python API, with direct HTTP requests.
Since Python API actually works over the HTTP requests to BrainBox server,
and the API calls are translated into HTTP requests automatically with `brainbox.framework.common.marshalling` module,
I can guarantee that it works.
However, it is not yet nicely documented.

## Manage the controllers

Installation, running, stopping and self-testing of deciders is available on
`http://127.0.0.1:8090/html/controllers/status`.
The web-page is hopefully self-explanatory.

The web-page also allows you to start the container.
Since most of the containers have web-server inside, you can call the endpoints of these web-servers
instead of BrainBox.
These servers, however, are not nicely written, don't have the documentation
and there is no plan to write this documentation in the future,
because it's a massive work that will have little sense,
since BrainBox implements the calls itself.

## Run the tasks

To run the deciders via BrainBox, we have two endpoints, `/jobs/add` and `/jobs/join`.

`jobs/add` accepts a list of dictionaries, each describing one job.
What we did above with `BrainBox.Task.call(HelloBrainBox)` was actually a definition of the job with API.
Job has the following fields:

* `id`: a unique string id of the job
* `decider`: the name of the decider, like `"Boilerlate"` string
* `method`: the method of decider class we're running. Can be None if the class defines `__call__` method and is therefore callable itself.
* `decider_parameter`: decider's parameter, usually None
* `arguments`: arguments of the method as dictionary.
* `info`: arbitrary data that is associated with the job, but doesn't have any effect on it.
* `batch`: jobs in e.g. `Collector`'s packs are organized in batches, so in the web-interface it may be seen what percentage
   of this collective job is finished.
* `dependencies`: a dictionary with keys set to the names of the arguments of the method, and values as id of the dependent tasks.
  If the key starts with `*`, the dependent task will be waited for, but it's value won't be used.
* `ordering_token`: None or an arbitrary string that helps BrainBox arrange the jobs to minimize the model switching.
   Something like `<larger_model_name>/<smaller_model_name>/<even_smaller_model_name>` is usually sufficient.

Simply the list of such dictionaries to the BrainBox server and it will add the tasks to the queue,
returning the control immediately.
To block your process until the tasks are finished, use `/jobs/join` endpoint,
and provide it with the list of `id` of the jobs you want to wait for.
As a result, `/jobs/join` will return a list of arbitrary objects that correspond to the list of `id`.

```python
import requests
import uuid

address = api.address
id = str(uuid.uuid4())

reply = requests.post(f'http://{address}/jobs/add', json=
{
    "arguments": {
        "jobs": [
            {
                "id": id,
                "decider": "HelloBrainBox",
                "method": "json",
                "decider_parameter": None,
                "arguments": {
                    "argument": "Hello, HTTP"
                }
            }
        ]
    }
})
if reply.status_code != 200:
    raise ValueError(f"Endpoint returned {reply.status_code}\n{reply.json()['error']}")

reply = requests.get(f"http://{address}/jobs/join", json=
{
    "arguments": {
        "ids": [
            id
        ]
    }
})

if reply.status_code != 200:
    raise ValueError(f"Endpoint returned {reply.status_code}\n{reply.json()['error']}")

result = reply.json()['result'][0]
test_case.assertDictEqual(
    {
        'argument': 'Hello, HTTP',
        'model': 'no_parameter',
        'setting': 'default_setting'
    },
    result
)
```






