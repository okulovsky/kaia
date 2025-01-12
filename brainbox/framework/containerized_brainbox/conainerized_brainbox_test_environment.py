from brainbox.framework.containerized_brainbox import BrainBoxRunner
from brainbox.framework import BrainBoxApi, Loc
from threading import Thread


class ContainerizedBrainboxTestEnvironment:
    def __init__(self, runner: BrainBoxRunner|None = None):
        if runner is None:
            runner = BrainBoxRunner(Loc.root_folder, 8090, True, debug=True)
        self.runner = runner

    def _run_container_thread(self):
        self.runner.get_deployment().run()

    def __enter__(self):
        self.runner.get_deployment().stop().remove().build()
        Thread(target=self._run_container_thread).start()
        api = BrainBoxApi('127.0.0.1:8090')
        api.wait(60)
        return api

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.runner.get_deployment().stop().remove()