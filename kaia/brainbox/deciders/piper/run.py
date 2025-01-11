from kaia.brainbox.deciders.piper.installer import PiperInstaller
from kaia.brainbox.deciders.piper.settings import PiperSettings

if __name__ == "__main__":
    settings = PiperSettings()
    installer = PiperInstaller(settings)
    installer.install()
    installer.brainbox_self_test()

