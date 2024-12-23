from brainbox.deciders import CoquiTTS
from brainbox import BrainBoxApi, BrainBoxTask

if __name__ == '__main__':
    installer = CoquiTTS.Controller()
    installer.install()
    installer.self_test()
    #installer.run_notebook()



