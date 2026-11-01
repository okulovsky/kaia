from chara.common import Chara
from chara.nlu.testbed import TestbedIntents, run_nlu_testbed, Stt


if __name__ == '__main__':
    run_nlu_testbed(
        TestbedIntents.get_templates(),
        Chara.Apis.content_folder/'nlu_testbed',
        stt=Stt.NEMOTRON_LANGUAGES,
        deploy_models=False
    )
