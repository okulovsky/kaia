from kaia.brainbox.deciders.denoiser.installer import DenoiserInstaller
from kaia.brainbox.deciders.denoiser.settings import DenoiseSettings

if __name__ == '__main__':
    installer = DenoiserInstaller(DenoiseSettings)
    installer.run_in_any_case_and_create_api()
