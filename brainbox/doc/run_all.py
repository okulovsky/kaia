from .p01_installation_and_self_test import *
from .p02_simple_runs import *
from .p03_downloads import *
from .p04_uploads import *
from .p05_resources import *
from .p06_dependent_tasks import *
from .p07_without_api import *

def run_all(api: BrainBox.Api, test_case: TestCase|None = None):
    if test_case is None:
        test_case = TestCase()

    print('Uninstalling HelloBrainBox')
    api.controller_api.uninstall(HelloBrainBox, True)

    print('Installing HelloBrainBox')
    install(test_case, api)

    print("Self-testing HelloBrainBox")
    self_test(test_case, api)

    print("Running decider without parameter")
    run_without_parameters(test_case, api)

    print("Running decider with parameter")
    run_with_parameter(test_case, api)

    print("Test downloading files")
    downloads(test_case, api)

    print("Test uploading files")
    uploads(test_case, api)

    print("Resources")
    resources(test_case, api)

    print("Model installation")
    model_installation(test_case, api)

    print("Dependent tasks")
    dependent_tasks(test_case, api)

    print("Collector")
    collector(test_case, api)

    print("Running without API")
    pure_http(test_case, api)

    print("ALL GOOD")