from .installer import OpenVoiceInstaller
from .settings import OpenVoiceSettings

if __name__ == "__main__":
    settings = OpenVoiceSettings()
    installer = OpenVoiceInstaller(settings)
    installer.install()
    installer.run()
