from brainbox import BrainBox
api = BrainBox.Api("http://127.0.0.1:8090")

if __name__ == '__main__':
    """
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
    """

    from brainbox.deciders import HelloBrainBox

    api.controllers.install.execute(HelloBrainBox)

    """
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
    """

    import requests, webbrowser, tempfile
    from pathlib import Path

    key = api.controllers.self_test.start(HelloBrainBox)
    api.controllers.self_test.join(key)
    report = api.controllers.self_test.html_report(key)

    test_case_test_path = Path(tempfile.gettempdir()) / 'test_report.html'
    with open(test_case_test_path, 'w', encoding='utf-8') as file:
        file.write(report)

    """

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
    """