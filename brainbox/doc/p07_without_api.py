from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase

def pure_http(test_case: TestCase, api: BrainBox.Api):
    """
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

    To run the deciders via BrainBox, we have two endpoints,
    `/tasks-service/base-add` and `/tasks-service/base-join`.

    `tasks-service/base-add` accepts a list of job descriptions.
    What we did above with `HelloBrainBox.new_task()` was actually a definition of the job with API.
    Job has the following fields:

    * `id`: a unique string id of the job
    * `decider`: the name of the decider, like `"HelloBrainBox"` string
    * `method`: the method of decider class we're running. Can be None if the class defines `__call__` method and is therefore callable itself.
    * `parameter`: decider's parameter, usually None
    * `arguments`: arguments of the method as dictionary.
    * `info`: arbitrary data that is associated with the job, but doesn't have any effect on it.
    * `batch`: jobs in e.g. `Collector`'s packs are organized in batches, so in the web-interface it may be seen what percentage
       of this collective job is finished.
    * `dependencies`: a dictionary with keys set to the names of the arguments of the method, and values as id of the dependent tasks.
      If the key starts with `*`, the dependent task will be waited for, but it's value won't be used.
    * `ordering_token`: None or an arbitrary string that helps BrainBox arrange the jobs to minimize the model switching.
       Something like `<larger_model_name>/<smaller_model_name>/<even_smaller_model_name>` is usually sufficient.

    POST the list of such dictionaries to the BrainBox server and it will add the tasks to the queue,
    returning the control immediately.
    To block your process until the tasks are finished, use `/tasks-service/base-join` endpoint,
    and provide it with the list of `id` of the jobs you want to wait for.
    As a result, `/tasks-service/base-join` will return a JSON array of results corresponding to the provided ids.

    """
    import requests
    import uuid

    address = api.address
    id = str(uuid.uuid4())

    reply = requests.post(f'http://{address}/tasks-service/base-add', json=
    {
        "jobs": [
            {
                "id": id,
                "decider": "HelloBrainBox",
                "method": "sum",
                "parameter": None,
                "arguments": {
                    "a": 2,
                    "b": 4
                },
                "info": None,
                "batch": None,
                "ordering_token": None,
                "dependencies": {}
            }
        ]
    })
    if reply.status_code != 200:
        raise ValueError(f"Endpoint returned {reply.status_code}\n{reply.text}")

    reply = requests.post(f"http://{address}/tasks-service/base-join", json=
    {
        "ids": [
            id
        ]
    })

    if reply.status_code != 200:
        raise ValueError(f"Endpoint returned {reply.status_code}\n{reply.text}")

    result = reply.json()[0]
    test_case.assertEqual(6, result)
