from chara.common import Chara
from chara.nlu.testbed import TestbedIntents, run_nlu_testbed


if __name__ == '__main__':
    run_nlu_testbed(TestbedIntents.get_templates(), Chara.Apis.content_folder/'nlu_testbed')

