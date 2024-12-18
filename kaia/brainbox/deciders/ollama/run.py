import requests
from kaia.brainbox.deciders.ollama import OllamaInstaller, OllamaSettings, Ollama



if __name__ == '__main__':
    installer = OllamaInstaller(OllamaSettings())
    #api: Ollama = installer.run_in_any_case_and_create_api()
    #installer.warmup(None)
    #print(api.with_model('llama3.2:1b').question("How to cook zurek?"))
    #installer.cooldown(None)
    installer.brainbox_self_test()







