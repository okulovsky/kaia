from brainbox import BrainBox
from foundation_kaia.releasing.mddoc import ControlValue
api = BrainBox.Api("http://127.0.0.1:8090")

sum_result = ControlValue.mddoc_define_control_value(6)
voiceover_1_result = ControlValue.mddoc_define_control_value({'text': 'hello', 'model': '[LOADED] /resources/models/google'})
voiceover_2_result = ControlValue.mddoc_define_control_value({'text': 'hey', 'model': '[LOADED] /resources/models/google'})
voiceover_3_result = ControlValue.mddoc_define_control_value({'text': 'hola', 'model': '[LOADED] /resources/models/facebook'})

if __name__ == '__main__':
    """
    ### Call an endpoint

    This will execute the method `HelloBrainBox::sum` on the server side.
    """
    from brainbox.deciders import HelloBrainBox

    result = api.execute(HelloBrainBox.new_task().sum(2, 4))

    """
    The result will be:
    """

    sum_result.mddoc_validate_control_value(result)

    """
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

    ```
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
    """

    import json

    result = api.execute(HelloBrainBox.new_task().voiceover('hello', HelloBrainBox.Models.google))
    file = api.cache.read(result)
    content = json.loads(file)

    """
    Since this endpoint plays the role of voiceover, it does not return the content as-is 
    (otherwise the BrainBox database would be very soon overflown by gygabytes of the images and sounds).
    Instead, the content is placed in a file, and the name of this file is returned. 
    The content is then retrieved via `api.cache`. 
    
    The `HelloBrainBox.Models` enum lists the pre-configured models.
    You can also pass the model name as a plain string.
    
    The result will be:
    """
    voiceover_1_result.mddoc_validate_control_value(content)

    """
    Since the model was already loaded by the previous call, you may now omit the argument:
    
    """
    result = api.execute(HelloBrainBox.new_task().voiceover('hey'))
    file = api.cache.read(result)
    content = json.loads(file)

    """
    The content will be:
    """
    voiceover_2_result.mddoc_validate_control_value(content)

    """
    You can also switch the model manually:
    """
    api.execute(HelloBrainBox.new_task().load_model(HelloBrainBox.Models.facebook))
    result = api.execute(HelloBrainBox.new_task().voiceover('hola'))
    file = api.cache.read(result)
    content = json.loads(file)

    """
    That will produce:
    """

    voiceover_3_result.mddoc_validate_control_value(content)

    """
    However, this is not recommended. 
    The best way is to always specify the model in the task itself to avoid interdependencies 
    between tasks runs. 
    The model loading setup that is used by HelloBrainBox is shared between many other deciders
    via the interface `IModelLoadingSupport` and `SingleModelStorage`, defined in foundation_kaia.brainbox_utils.
    """
