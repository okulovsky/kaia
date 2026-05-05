from foundation_kaia.brainbox_utils import IModelInstallingSupport, IInstallingSupport, Installer
from .docker_marshalling_controller import DockerMarshallingController

class PostInstallProcess:
    def __init__(self, controller: 'DockerMarshallingController'):
        self.controller = controller
        self.running_api = None
        self.instance_id = None

    def get_running_api(self):
        if self.running_api is not None:
            return self.running_api
        self.instance_id = self.controller.run(None) #All the new generation containers are without parameter!
        self.running_api = self.controller.find_api(self.instance_id)
        return self.running_api

    def get_models_to_install(self, installer: Installer) -> dict:
        if not hasattr(self.controller.settings, 'models_to_install'):
            print("No installable models")
            return {}
        all_models = self.controller.settings.models_to_install
        print("All installable models")
        if isinstance(all_models, dict):
            return {k:v for k, v in all_models.items() if not installer.is_model_installed(k)}
        try:
            all_models_list = list(all_models)
        except:
            raise TypeError(f"settings.models_to_install must be dict or convertible to list, but was {type(all_models)}")
        return {k:k for k in all_models_list if not installer.is_model_installed(k)}

    def __call__(self):
        try:
            installer = self.controller.get_installer()
            if installer is None:
                print("No post_install needed (get_installer returned None)")
                return

            if not installer.is_installed():
                print("The service is not installed, installing...")
                api = self.get_running_api()
                if not isinstance(api,IInstallingSupport):
                    raise ValueError("API doesn't implement IInstallingSupport, which is needed for installation")
                print("Sending the installation request")
                api.install()
                print("Installed")
            else:
                print("The service is already installed")

            models_to_install = self.get_models_to_install(installer)
            if len(models_to_install) > 0:
                print("Installing models: "+", ".join(models_to_install))
                api = self.get_running_api()
                if not isinstance(api, IModelInstallingSupport):
                    raise ValueError(f"API doesn't implement IModelDownloadingController, but models need to be downloaded: {', '.join(models_to_install)}")
                for model, model_spec in models_to_install.items():
                    print("Sending the installation request for model: "+model)
                    api.download_model(model, model_spec)
            else:
                print("Models are already installed")
        finally:
            if self.instance_id is not None:
                self.controller.stop(self.instance_id)

