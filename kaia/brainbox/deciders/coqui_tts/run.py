from kaia.brainbox.deciders.coqui_tts import CoquiTTSInstaller, CoquiTTSSettings

if __name__ == '__main__':
    installer = CoquiTTSInstaller(CoquiTTSSettings())
    installer.install()
    installer.brainbox_self_test()


