from brainbox.deciders import ResembleEnhance
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    installer = ResembleEnhance.Controller()
    #resolve_dependencies(installer)

    installer.install()
    installer.self_test()

    #test_on_arm64(installer)

