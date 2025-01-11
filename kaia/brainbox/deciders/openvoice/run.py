from kaia.brainbox.deciders.openvoice.installer import OpenVoiceInstaller
from kaia.brainbox.deciders.openvoice.settings import OpenVoiceSettings

if __name__ == "__main__":
    settings = OpenVoiceSettings()
    installer = OpenVoiceInstaller(settings)
    installer.install()
    installer.brainbox_self_test()
