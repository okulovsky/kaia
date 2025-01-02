from brainbox import BrainBox
from brainbox.deciders import Boilerplate
from unittest import TestCase

def resources(test_case: TestCase, api: BrainBox.Api):
    """
    ## Advanced techniques

    ### Browse the resources

    Many deciders have _resources_: files, typically model files, that are passed to the containers and used for inference.
    It is impractical to store them inside containers, and so BrainBox stores them in the host's file system:
    each decider has its own resource folder, which is mounted to the container.

    Aside from models, the training data may be stored in resources instead of file cache, as training data
    are easier to organize with folder structure and predictable filenames.

    This endpoint demonstrates that the server indeed has an access to the resources:
    Boilerplate reads them and returns the dictionary of keys set to filenames,
    and values set to file content.
    These resources are created by Boilerplate controller as a part of installation procedure.
    """
    resources = api.execute(BrainBox.Task.call(Boilerplate).resources())
    test_case.assertDictEqual(
        {'nested/resource': 'Boilerplate nested resource', 'resource': 'Boilerplate resource'},
        resources
    )

    """
    However, a uniform access to all the resources is provided by API, e.g. to list all the resources:
    """

    resources = api.controller_api.list_resources(Boilerplate, '/')
    test_case.assertListEqual(
        ['resource', 'nested/resource'],
        resources
    )


def model_installation(test_case: TestCase, api: BrainBox.Api):
    """
    ### Download a custom model

    Many deciders can run with different models, and these models need to be downloaded.
    All the deciders load some models at the installation time to allow self-test to run.
    However, more models are usually needed.

    Sometimes the containers are able to download these models themselves,
    but often enough the models need to be downloaded separately.

    This action can be triggered via `api`:
    """

    api.controller_api.download_models(Boilerplate, [Boilerplate.Model('google', 'http://www.google.com')])
    resources = api.controller_api.list_resources(Boilerplate, '/models')
    test_case.assertListEqual(['models/google'], resources)







