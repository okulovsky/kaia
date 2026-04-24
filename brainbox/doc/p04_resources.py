from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from foundation_kaia.releasing.mddoc import ControlValue
api = BrainBox.Api("http://127.0.0.1:8090")

models_to_install = ControlValue.mddoc_define_control_value({'google': HelloBrainBox.ModelSpec(url='https://google.com'), 'facebook': HelloBrainBox.ModelSpec(url='https://facebook.com')})
resources_before = ControlValue.mddoc_define_control_value(['facebook', 'google'])
resources_after = ControlValue.mddoc_define_control_value(['facebook', 'google', 'microsoft'])

if __name__ == '__main__':
    """
    ## Advanced techniques

    ### Models' management

    Many deciders support multiple models that need to be downloaded before use.
    The models a decider downloads during installation are declared in
    `Settings.models_to_install`:
    
    """
    models = HelloBrainBox.Settings.models_to_install

    """
    The `models` variable is:
    """

    models_to_install.mddoc_validate_control_value(models)

    """

    These models are downloaded automatically when the decider is installed.
    You can list them using the resources API:
    """

    resources = api.resources(HelloBrainBox).list('models', glob=True)

    """
    The result should be:
    """

    resources_before.mddoc_validate_control_value(lambda: 'facebook' in resources and 'google' in resources)

    """
    The actual result may be different if you previously installed other models.

    Each decider has its own _resource folder_ on the host file system,
    mounted into the container. Model files live in the `models/` subfolder
    of that resource folder.

    If you need to download an additional model that was not included in
    `models_to_install`, you can trigger the download via BrainBox:
    """

    api.execute(
        HelloBrainBox.new_task().download_model(
            'microsoft',
            HelloBrainBox.ModelSpec('http://microsoft.com')
        )
    )

    resources = api.resources(HelloBrainBox).list('models', glob=True)

    """
    The result should be:
    """

    resources_after.mddoc_validate_control_value(lambda: 'facebook' in resources and 'google' in resources and 'microsoft' in resources)

    """
    The `download_model` endpoint is provided by `IModelInstallingSupport`.
    After the download, the model is registered in the decider's
    `installation.yaml` and available for use in subsequent calls.
    """
