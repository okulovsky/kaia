from kaia.brainbox.deciders.automatic1111.install import Automatic1111Installer, Automatic1111Settings
import requests

if __name__ == '__main__':
    installer = Automatic1111Installer(Automatic1111Settings())
    #installer.install()
    #installer.run()
    api = installer.create_api()
    opt = requests.get(f'http://{api.address}:{api.settings.port}/sdapi/v1/options').json()
    print(opt['sd_model_checkpoint'])
    opt['sd_model_checkpoint'] = 'model name'
    #post('/sdapi/v1/options', opt)
    #print(api.text_to_image('cute little cat', ''))