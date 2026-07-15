import hashlib
import re
from ..architecture import IController, TSettings
from ...deployment import IImageSource, IImageBuilder, Deployment, LocalImageSource, IContainerRunner, Command
import shutil
from .runner import BrainBoxRunner
from .run_configuration import RunConfiguration
import os

class DockerController(IController[TSettings]):
    # region Abstract methods
    def get_image_source(self) -> IImageSource:
        return LocalImageSource(self.get_snake_case_name())

    def get_image_builder(self) -> IImageBuilder|None:
        return None

    # endregion

    def get_executor(self):
        return self.context.executor

    def get_deployment(self, runner: IContainerRunner|None = None):
        return Deployment(
            self.get_image_source(),
            runner,
            self.get_executor(),
            self.get_image_builder()
        )


    def find_self_in_list(self, all_images_installed: tuple[str,...]):
        image = self.get_image_source().get_image_name().split(':')[0]
        if image in all_images_installed:
            return image
        else:
            return None

    def get_container_name(self, parameter: str | None = None) -> str:
        base = self.get_image_source().get_container_name()
        if parameter is None:
            return base
        sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', parameter)[:40]
        digest = hashlib.sha1(parameter.encode('utf-8')).hexdigest()[:6]
        return f'{base}-{sanitized}-{digest}'

    def install(self):
        self.context.api_callback.log("Stopping running instances, if any")
        self.stop_all()
        self.context.api_callback.log("Running pre-install")
        self.pre_install()
        self.context.api_callback.log("Stopping the current container, if exists")
        self.get_deployment().stop()
        self.context.api_callback.log("Removing the current container, if persists")
        self.get_deployment().remove()
        self.context.api_callback.log("Building/pulling image")
        self.get_deployment().obtain_image()
        self.context.api_callback.log("Running post-install")
        self.post_install()
        self.context.api_callback.log("DONE")

    def pre_install(self):
        pass

    def post_install(self):
        pass

    def uninstall(self, purge: bool = False):
        self.stop_all()
        self.get_deployment().stop().remove()
        images = self.get_image_source().get_relevant_images(self.get_executor())
        for image in images:
            self.get_executor().execute(['docker', 'rmi', image])
        if purge:
            for filename in os.listdir(self.resource_folder()):
                file_path = self.resource_folder()/filename
                if file_path.is_file():
                    os.unlink(file_path)  # Remove file or symlink
                if file_path.is_dir():
                    shutil.rmtree(file_path)  # Remove directory and its contents
            shutil.rmtree(self.resource_folder())

    def run_with_configuration(self, configuration: RunConfiguration, container_name: str | None = None, monitor_function = print) -> str:
        container_name = container_name or self.get_image_source().get_container_name()
        command = configuration.generate_command(
            container_name,
            self.get_image_source().get_image_name(),
            self.context
        )
        print(" ".join(command))
        result = self.get_executor().execute(command, Command.Options(monitor_output=monitor_function))
        return result[:12]

    def stop(self, instance_id: str):
        self.get_executor().execute(['docker','stop',instance_id], Command.Options(ignore_exit_code=True))
        self.get_executor().execute(['docker', 'rm', instance_id], Command.Options(ignore_exit_code=True))

    def get_running_instances_id_to_parameter(self) -> dict[str, str|None]:
        return {i.instance_id: i.parameter for i in self.context.instance_registry.get_instances(self.get_name())}

    def run_auxiliary_configuration(self, cfg):
        runner = BrainBoxRunner(self.context, cfg, False)
        runner.run(
            self.get_image_source().get_image_name(),
            self.get_image_source().get_container_name(),
            self.get_executor()
        )


