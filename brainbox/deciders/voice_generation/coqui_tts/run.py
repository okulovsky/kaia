from brainbox.deciders import CoquiTTS
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    installer = CoquiTTS.Controller()
    #resolve_dependencies(installer)

    installer.install()
    installer.self_test()
    #installer.run_notebook()



