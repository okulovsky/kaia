import sys
from pathlib import Path
from kaia.infra import rebooter, Loc
import subprocess


if __name__ == '__main__':
    if subprocess.call('docker ps') != 0:
        print('Docker is not running. Please install/run docker before running BrainBox')
        exit(1)

    checker = rebooter.WebServerAvailabilityChecker('http://127.0.0.1:8090/status', 'OK')
    controller = rebooter.SubprocessController([sys.executable, str(Path(__file__).parent/'run_brain_box.py')])
    rebooter = rebooter.Rebooter(checker, controller, Loc.data_folder/'brain_box_rebooter_log.txt')
    rebooter.run()

