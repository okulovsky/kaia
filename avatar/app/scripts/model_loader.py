import urllib.request
from pathlib import Path

DEFAULT_MODEL_NAME = 'vosk-model-small-en-us-0.15.zip'

def download_vosk_model(folder: Path, model_name: str = DEFAULT_MODEL_NAME):
    """
    Check if the model is already downloaded, if not, download it in the folder
    """
    folder.mkdir(parents=True, exist_ok=True)
    model_path = folder / model_name
    if model_path.exists():
        return
    url = 'https://alphacephei.com/vosk/models/' + model_name
    print(f"Downloading Vosk model from {url} ...")
    urllib.request.urlretrieve(url, model_path)
    print(f"Vosk model saved to {model_path}")
