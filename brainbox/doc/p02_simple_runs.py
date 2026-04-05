from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase

def computation(test_case: TestCase, api: BrainBox.Api):
    """
    ### Call an endpoint

    This will execute the method `HelloBrainBox::sum` on the server side.
    """

    result = api.execute(HelloBrainBox.new_task().sum(2, 4))
    test_case.assertEqual(6, result)

    """
    The BrainBox will run the container for the HelloBrainBox decider.
    This container has a web-server inside, and `HelloBrainBox::sum`
    connects to this web-server and performs the required operation.
    The result (in this case, a number) is then returned to the caller.
    
    BrainBox is smart and tries to minimize the containers' runs.
    If several tasks for the same decider have arrived,
    this decider will be set up, and then all these tasks will be executed
    before the tasks for other deciders.
    """

def call_with_model(test_case: TestCase, api: BrainBox.Api):
    """
    ### Select a model via parameter

    For a very few deciders, the model must be selected before running the container,
    and this is done with container parameter. Ollama is one of such deciders,
    so the call would be:

    ```
    result = api.execute(Ollama.new_task(parameter='mistral-small').question("What's the recipe for borsh?"))
    ```

    Also, new_task can specify:
    * id, in case you want the job to have a non-random ID
    * info: arbitrary JSON assotiate with a task, helpful when you want to associate some tags with a task and retrieve them later

    ### Select a model as a method's argument

    Modern deciders do not use a container parameter to select a model.
    Instead, the model is passed directly as a method argument.
    This is more flexible: multiple models can be used within the same
    container session, and the model is loaded on demand.

    `HelloBrainBox::voiceover` accepts an optional `model` argument.
    The available models are listed in `HelloBrainBox.Settings.models_to_install`
    and are downloaded automatically during installation.
    """

    import json

    result = api.execute(HelloBrainBox.new_task().voiceover('hello', HelloBrainBox.Models.google))
    file = api.cache.read_file(result)
    content = json.loads(file.content)
    test_case.assertEqual('hello', content['text'])
    test_case.assertIn('google', content['model'])

    """
    As you can see, the model is specified as a method argument, not as a
    container parameter.

    The `HelloBrainBox.Models` enum lists the pre-configured models.
    You can also pass the model name as a plain string.
    """
