from chara.common import Chara
from chara.nlu.scripts import *
from chara.nlu.testbed import TestbedIntents


if __name__ == '__main__':
    create_dataset(TestbedIntents.get_templates(), folder=Chara.Apis.content_folder/'nlu_testbed')
    #create_negatives(folder=Chara.Apis.content_folder/'nlu_testbed')
    print(train_ultimate_nlu(Chara.Apis.content_folder / 'nlu_testbed'))
    pass