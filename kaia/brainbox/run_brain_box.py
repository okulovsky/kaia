from kaia.brainbox import BrainBox
from kaia.infra import Loc
from kaia.infra.comm import  Sql

if __name__ == '__main__':
    comm = Sql.file(Loc.data_folder/'brain_box_db')
    server = BrainBox().create_web_service(comm)
    server()



