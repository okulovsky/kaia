from kaia.brainbox.deciders.oobabooga.installer import OobaboogaInstaller, OobaboogaSettings
from unittest import TestCase

if __name__ == '__main__':
    settings = OobaboogaSettings()
    installer = OobaboogaInstaller(settings)
    installer.install(); exit(0)
    installer.kill(); installer.run_with_given_model(settings.models_to_download[1].name)
    api = installer.create_api()
    import requests
    reply = requests.post(f'http://{api.address}/v1/chat/completions', json={
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ],
    "mode": "instruct",
    "instruction_template": "Alpaca"
  })
    print(reply.content)



