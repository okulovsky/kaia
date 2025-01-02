from brainbox.tools.deployment import BrainBoxRunner
from brainbox.framework import Loc

if __name__ == '__main__':
    runner = BrainBoxRunner(Loc.root_folder, 8090, True)
    runner.get_deployment().stop().remove().build().run()
