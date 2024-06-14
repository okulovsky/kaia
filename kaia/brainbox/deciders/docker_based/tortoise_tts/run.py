from kaia.brainbox.deciders.docker_based.tortoise_tts.installer import TortoiseTTSSettings, TortoiseTTSInstaller
from unittest import TestCase

if __name__ == '__main__':
    settings = TortoiseTTSSettings()
    installer = TortoiseTTSInstaller(settings)
    installer.install()
    #print(' '.join(installer.server_endpoint.get_deployment().docker_run.get_run_command(installer.server_endpoint.get_deployment().builder.get_local_name())))
    installer.self_test(TestCase())