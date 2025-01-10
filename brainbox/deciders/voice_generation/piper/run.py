from .installer import PiperInstaller
from .settings import PiperSettings

if __name__ == "__main__":
    settings = PiperSettings()
    installer = PiperInstaller(settings)
    installer.install()
    installer.run()
    # installer.brainbox_self_test()

