from .p01_installation_and_self_test import *
from .p02_simple_runs import *
from .p03_downloads import *
from .p04_uploads import *
from .p05_resources import *
from .p06_dependent_tasks import *
from .p07_without_api import *

NAME = 'HelloBrainBox'

def run_all(api: BrainBox.Api, test_case: TestCase|None = None):
    if test_case is None:
        test_case = TestCase()

    print('Uninstalling HelloBrainBox')
    api.controllers.uninstall(HelloBrainBox, True)

    print('Installing HelloBrainBox')
    install(test_case, api)

    print("Self-testing HelloBrainBox")
    self_test(test_case, api)

    print("Running simple computation")
    computation(test_case, api)

    print("Running with model argument")
    call_with_model(test_case, api)

    print("Test downloading files")
    downloads(test_case, api)

    print("Test uploading files")
    uploads(test_case, api)

    print("Model management and streaming")
    model_management(test_case, api)

    print("Streaming and long-running processes")
    streaming(test_case, api)

    print("Dependent tasks")
    dependent_tasks(test_case, api)

    print("Collector")
    collector(test_case, api)

    print("Media library")
    media_library(test_case, api)

    print("Running without API")
    pure_http(test_case, api)

    print("ALL GOOD")
