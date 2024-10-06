from kaia.brainbox.deciders.rhasspy_kaldi import RhasspyKaldiSettings, RhasspyKaldiInstaller

if __name__ == '__main__':
    installer = RhasspyKaldiInstaller(RhasspyKaldiSettings())
    installer.install()
    installer.brainbox_self_test()
    