from brainbox import BrainBox
from brainbox.deciders.text.ollama import Ollama

MODEL = 'llama3.1:8b'

api = BrainBox.Api('127.0.0.1:8090')
api.controller_api.download_models(Ollama, [{'name': MODEL}])
print(f"Downloaded {MODEL}")
