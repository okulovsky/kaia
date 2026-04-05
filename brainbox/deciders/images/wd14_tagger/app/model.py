from foundation_kaia.brainbox_utils import Installer


class WD14TaggerInstaller(Installer[str]):
    def _execute_installation(self):
        pass

    def _execute_model_downloading(self, model: str, model_spec: str):
        from tagger.interrogators import interrogators
        interrogator = interrogators[model]
        interrogator.use_cpu()
        interrogator.load()

    def _execute_model_loading(self, model: str, model_spec: str):
        from tagger.interrogators import interrogators
        interrogator = interrogators[model]
        interrogator.use_cpu()
        interrogator.load()
        return interrogator
