from kaia.brainbox.deciders.open_tts import OpenTTSInstaller, OpenTTSSettings

if __name__ == '__main__':
    installer = OpenTTSInstaller(OpenTTSSettings())
    installer.brainbox_self_test()