from .container_runner import BrainBoxRunner
from brainbox.framework import BrainBoxApi
from threading import Thread
from foundation_kaia.misc import Loc


class ContainerizedBrainboxTestEnvironment:
    def __init__(self, runner: BrainBoxRunner|None = None):
        if runner is None:
            runner = BrainBoxRunner(Loc.data_folder/'brainbox_in_container', 8090, True, debug=True)
        self.runner = runner

    def _run_container_thread(self):
        self.runner.get_deployment().run()

    def __enter__(self):
        self.runner.get_deployment().stop().remove().build()
        Thread(target=self._run_container_thread).start()
        api = BrainBoxApi('http://127.0.0.1:8090')
        api.wait_for_connection(60)
        return api

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.runner.get_deployment().stop().remove()