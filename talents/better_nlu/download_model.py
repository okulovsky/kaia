from brainbox import BrainBox
from brainbox.deciders.text.ollama import Ollama
from talents.better_nlu.model import get_model

api = BrainBox.Api('127.0.0.1:8090')
Ollama.Controller().download_models(Ollama.Model(get_model()))
print(f"Downloaded {get_model()}")
