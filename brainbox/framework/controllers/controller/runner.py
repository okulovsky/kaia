from ...deployment import IContainerRunner, IExecutor, Command
from dataclasses import dataclass
from .controller_context import ControllerContext
from .run_configuration import RunConfiguration

@dataclass
class BrainBoxRunner(IContainerRunner):
    context: ControllerContext
    configuration: RunConfiguration
    return_output: bool

    def run(self, image_name: str, container_name: str, executor: IExecutor):
        command = self.configuration.generate_command(container_name, image_name, self.context)
        result = executor.execute(command, Command.Options(return_output=self.return_output))
        if result is None:
            return result
        return result.strip()

