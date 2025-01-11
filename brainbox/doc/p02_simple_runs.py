from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from unittest import TestCase

def run_without_parameters(test_case:TestCase, api: BrainBox.Api):
    """
    ### Call an endpoint

    This will execute the method HelloBrainBox::json on the server side.
    """

    result = api.execute(BrainBox.Task.call(HelloBrainBox).json("Hello"))
    test_case.assertDictEqual(
        {
            'argument': 'Hello',
            'model': 'no_parameter',
            'setting': 'default_setting'
        },
        result
    )

    """
    The BrainBox will run the container for the HelloBrainBox decider.
    This container has a web-server inside, and HelloBrainBox::json 
    connects to this web-server and performs the required operation.
    The result (in this case, `dict`) is then returned to the caller.
    As you see, `argument` equals to the argument the code provides.
    
    BrainBox is smart and tries to minimize the containers' runs.
    If several tasks for same decider have arrived,
    this decider will be set up, and then all these tasks will be executed
    before the tasks for other deciders.
    """

def run_with_parameter(test_case: TestCase, api: BrainBox.Api):
    """
    ### Call an enpoint with a parameter

    Few deciders have parameters: a string argument that will be fed to the container
    on the start, and may modify its behaviour. It's sometimes required
    when you don't build container from scratch, but use a ready container,
    which requires you to load the model on the startup, and in this case,
    `parameter` is this model's name.

    To pass the parameter, simply add it to `call` function:
    """

    result = api.execute(BrainBox.Task.call(HelloBrainBox, "parameter").json("Hello"))
    test_case.assertDictEqual(
        {
            'argument': 'Hello',
            'model': 'parameter',
            'setting': 'default_setting'
        },
        result
    )

    """
    As you can see, the `model` field is now set to `parameter`. 
    
    Most of the deciders do not have the parameter and load models dynamically, so normally you write
    `BrainBoxTask.call(DeciderClass).method(...)`
    
    Please ignore the `setting` field. 
    There is a possibility to adjust settings to the controllers,
    such as the port the internal web-server will be assigned for,
    or the list of models the controllers need to download,
    but so far there was never a necessity to adjust them manually.
    They are only used with the default values.
    """
