from brainbox.framework import OnDemandDockerApi, FileLike, FileIO, File, RunConfiguration
from .controller import BoilerplateOnDemandController
from .settings import BoilerplateOnDemandSettings

class BoilerplateOnDemand(OnDemandDockerApi[BoilerplateOnDemandSettings, BoilerplateOnDemandController]):
    def _monitor_progress(self, line: str):
        try:
            if not line.endswith('%'):
                return
            value = int(line[:-1])
            self.context.logger.report_progress(value/100)
        except:
            pass

    def execute(self, input: str):
        FileIO.write_text(input, self.controller.resource_folder()/'input')

        configuration = RunConfiguration(
            detach_and_interactive=False
        )
        self.controller.run_with_configuration(configuration, self._monitor_progress)

        return FileIO.read_text(self.controller.resource_folder()/'output')


    Controller = BoilerplateOnDemandController
    Settings = BoilerplateOnDemandSettings
