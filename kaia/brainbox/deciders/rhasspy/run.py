from kaia.brainbox.deciders.rhasspy import RhasspySettings, RhasspyInstaller

if __name__ == '__main__':
    installer = RhasspyInstaller(RhasspySettings())
    installer.reinstall()