from brainbox.deciders import WhisperX
from brainbox.framework import Loc
import dotenv
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    dotenv.load_dotenv(Loc.root_folder/'environment.env')
    controller = WhisperX.Controller()
    #resolve_dependencies(controller)

    controller.install()
    controller.self_test()