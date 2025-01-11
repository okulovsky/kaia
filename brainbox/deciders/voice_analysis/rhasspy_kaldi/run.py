from brainbox.deciders.voice_analysis.rhasspy_kaldi import RhasspyKaldi

if __name__ == '__main__':
    installer = RhasspyKaldi.Controller()
    installer.uninstall(True)
    installer.install()
    installer.self_test()
    