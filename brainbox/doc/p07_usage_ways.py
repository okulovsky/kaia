from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from foundation_kaia.releasing.mddoc import ControlValue
api = BrainBox.Api("http://127.0.0.1:8090")

result_value = ControlValue.mddoc_define_control_value(7)
pack_value = ControlValue.mddoc_define_control_value([9.0, 19.0])
json_value = ControlValue.mddoc_define_control_value({'text': 'Hello, world!', 'model': '[LOADED] /resources/models/google'})

if __name__ == '__main__':
    """
    # Usage ways
    
    ## Direct decider's calls
    
    Once the decider's instance is spawned, it can be accessed directly without any BrainBox at all.
    So it is possible for instance to build the container on your local machine, 
    deliver it to your remote machine via `docker pull/push`, run there and communicate directly to it,
    avoiding BrainBox queuing and caching.
    
    We will run the container with api:
    
    """

    api.controllers.run(HelloBrainBox)
    hello_api = HelloBrainBox.Api(f"http://127.0.0.1:{HelloBrainBox.Settings().connection.port}")
    hello_api.wait_for_connection()

    result = hello_api.sum(3,4)

    """
    The result will be:
    """

    result_value.mddoc_validate_control_value(result)

    """
    
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
    
    """

    import requests
    from pprint import pprint

    response = requests.get("http://127.0.0.1:20000/doc/json")
    response.raise_for_status()
    pprint(response.json())

    """
    Then, call the decider:
    """

    response = requests.post(
        "http://127.0.0.1:20000/hello-brain-box/sum",
        json={
            "a": 3,
            "b": 4
        }
    )
    response.raise_for_status()

    """
    `response.json` will contain: 
    """

    result_value.mddoc_validate_control_value(response.json())

    """
    ### HTTP access to the brainbox
    
    You can read documentation to the brainbox api at the same page `/doc/html`.
    
    All the controllers operations such as installing, starting, stopping the controller are supported in the API.
    However, some of these operations are needed only once (like installing), and some others are managed by
    BrainBox internally (such as starting the containers). Therefore, it makes more sense to use BrainBox GUI for them.    
    So we will cover only the API to create the tasks in this section.
    
    To add the task, you need to use `/tasks-service/base-add` with the list of tasks you want to create:
    
    """
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

    """
    We add two tasks where the second one depends on the first one. This is the correct ordering:
    the root comes last. This is because of the consistency checks: if the tasks depends on something,
    this something needs to be already in the queue.
    
    For the first task, we specify the `id` as we need to reuse it in the `dependencies` of the second task.
    For the second task, we may omit ID, it will be assigned automatically.   
    
    `base-add` endpoint returns the list of its. You can then wait for them to finish and retrieve the result:     
    """

    ids = response.json()
    response = requests.post(
        "http://127.0.0.1:8090/tasks-service/base-join",
        json = {
            "ids": ids
        }
    )
    response.raise_for_status()

    """
    `response.json` will be: 
    """

    pack_value.mddoc_validate_control_value(response.json())

    """
    Now, let's explore how to work with the files. The files are managed by `/cache` endpoints. 
    
    Let's upload the source file: 
    """

    id = str(uuid4())
    response = requests.post(
        f"http://127.0.0.1:8090/cache/upload/{id}",
        data = b'Hello, world!'
    )
    response.raise_for_status()



    """
    Then, we will run the decider:
    """

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

    """
    `result` will contain the file name, which needs to be retrieved from the cache:
    """

    response = requests.get(
        f"http://127.0.0.1:8090/cache/open/{result}",
    )
    response.raise_for_status()

    """
    Since `HelloBrainBox` is a demo server, this file is actually a JSON file disguised as a binary file. 
    """
    import json

    json_result = json.loads(response.text)

    """
    `json_result` is:
    """

    json_value.mddoc_validate_control_value(json_result)

    """
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
    
    """

    
    
    
