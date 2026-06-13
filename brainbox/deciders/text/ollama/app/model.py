import subprocess
from foundation_kaia.brainbox_utils import Installer


class OllamaInstaller(Installer[str]):
    def _execute_installation(self):
        pass

    def _execute_model_downloading(self, model: str, model_spec: str):
        subprocess.run(['/bin/ollama', 'pull', model], check=True)
