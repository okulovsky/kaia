from kaia.brainbox import BrainBox, BrainBoxSettings
from kaia.brainbox.core.planers import SmartPlanner, SimplePlanner
from kaia.infra import Loc
from kaia.infra.comm import  Sql
from functools import partial

if __name__ == '__main__':
    comm = Sql.file(Loc.data_folder/'brain_box_db')
    settings = BrainBoxSettings()
    settings.planner_factory = SimplePlanner
    server = BrainBox(settings).create_web_service(comm)
    server()



