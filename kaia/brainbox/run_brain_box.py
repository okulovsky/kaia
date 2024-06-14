import subprocess
import time
import traceback

from kaia.brainbox import BrainBox, BrainBoxSettings
from kaia.brainbox.core.planers import SmartPlanner, SimplePlanner
from kaia.infra import Loc
from kaia.infra.comm import  Sql
from functools import partial

if __name__ == '__main__':
    if subprocess.call('docker ps') != 0:
        print('Docker is not running. Please install/run docker before running BrainBox')
        exit(1)

    comm = Sql.file(Loc.data_folder/'brain_box_db')
    settings = BrainBoxSettings()
    settings.main_iteration_sleep = 1
    settings.raise_exceptions_in_main_cycle = False
    settings.planner_factory = SimplePlanner
    server = BrainBox(settings).create_web_service(comm)
    server()



