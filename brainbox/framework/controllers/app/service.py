import os
import shutil
import traceback
from dataclasses import dataclass
from threading import Thread

from ...common import Loc, FileIO
from ...common.marshalling import endpoint
from ..controller import TestReport, DockerWebServiceApi, ControllerRegistry, IController, IModelDownloadingController
from .interface import IControllerService, ControllerServiceStatus, InstallationReport, ControllersSetup

from .logging import Log, LoggingLocalExecutor, LogLogger
from yo_fluq import Query

@dataclass
class RunningInstallation:
    report: InstallationReport
    controller: IController
    thread: Thread|None = None

    def run(self):
        try:
            self.controller.install()
        except:
            error =  traceback.format_exc()
            self.report.error = error

    def exited(self):
        is_alive = self.thread.is_alive()
        return not self.thread.is_alive()


@dataclass
class ControllerServerSettings:
    registry: ControllerRegistry
    port: int = 8091

class ControllerService(IControllerService):
    def __init__(self, settings: ControllerServerSettings):
        self.settings = settings
        self.running_installation: RunningInstallation|None = None

    def get_controller(self, decider: str|type):
        name = ControllerRegistry.to_controller_name(decider)
        return self.settings.registry.get_controller(name)

    @endpoint(url='/controllers/install')
    def install(self, decider: str|type, join: bool = True) -> InstallationReport|None:
        if self.running_installation is not None and not self.running_installation.exited:
            raise ValueError("Another installation is in progress")
        self.running_installation = None

        controller = self.get_controller(decider)
        log = Log()
        controller.context._executor = LoggingLocalExecutor(log)
        controller.context._logger = LogLogger(log)

        installation_report = InstallationReport(controller.get_name(), log)
        installation = RunningInstallation(installation_report, controller)
        installation.thread = Thread(target=installation.run)
        installation.thread.start()
        self.running_installation = installation

        if join:
            return self.join_installation()


    @endpoint(url='/controllers/uninstall')
    def uninstall(self, decider: str|type, purge: bool = False):
        self.get_controller(decider).uninstall(purge)


    @endpoint(url='/controllers/run')
    def run(self, decider: str|type, parameter: str | None = None) -> str:
        if parameter == '':
            parameter = None
        return self.get_controller(decider).run(parameter)


    @endpoint(url='/controllers/stop')
    def stop(self, decider: str|type, instance_id: str):
        self.get_controller(decider).stop(instance_id)


    @endpoint(url='/controllers/join-installation')
    def join_installation(self) -> InstallationReport:
        if self.running_installation is None:
            raise ValueError("No installation is in progress")
        if not self.running_installation.exited():
            self.running_installation.thread.join()

        result = self.running_installation
        self.running_installation = None
        if result.report.error is not None:
            raise ValueError(f"Installation threw an exception\n{result.report.error}")
        return result.report




    @endpoint(url='/controllers/installation-report')
    def installation_report(self) -> InstallationReport:
        if self.running_installation is None:
            raise ValueError("No installation is in progress")
        return self.running_installation.report



    @endpoint(url='/controllers/status')
    def status(self):
        installation_statuses = self.settings.registry.get_installation_statuses()
        containers = []
        for name, installation_status in installation_statuses.items():
            if not installation_status.installed or installation_status.dockerless_controller:
                containers.append(ControllerServiceStatus.Controller(name, installation_status))
                continue

            container = self.get_controller(name)
            instances = []
            for instance_id, parameter in container.get_running_instances_id_to_parameter().items():
                address = None
                api = container.find_api(instance_id)
                if isinstance(api, DockerWebServiceApi):
                    address = api.address
                instances.append(ControllerServiceStatus.Instance(
                    instance_id,
                    parameter,
                    address
                ))

            report_path = (self.settings.registry.locator.self_test_path / name)
            has_report =  report_path.is_file()
            has_errors = False
            if has_errors:
                report = FileIO.read_pickle(report_path)
                if report.error is not None:
                    has_errors = True

            containers.append(ControllerServiceStatus.Controller(
                name,
                installation_status,
                has_report,
                has_errors,
                tuple(instances)
            ))

        installation = None
        if self.running_installation is not None and not self.running_installation.exited():
            installation = self.running_installation.report.name

        return ControllerServiceStatus(
            containers,
            installation
        )

    @endpoint(url='/controllers/self_test')
    def self_test(self, decider: str|type) -> TestReport:
        controller = self.get_controller(decider)
        return controller.self_test(output_folder=self.settings.registry.locator.self_test_path)


    @endpoint(url='/controllers/delete_self_test')
    def delete_self_test(self, decider: str|type):
        controller = self.get_controller(decider)
        path = Loc.self_test_path / controller.get_name()
        if path.is_file():
            os.unlink(path)


    def _inner_path(self, controller, path: str):
        while path.startswith('/'):
            path = path[1:]
        path = controller.context.resource_folder()/path
        path.relative_to(controller.context.resource_folder_root)
        return path

    @endpoint(url='/resources/list')
    def list_resources(self, decider: str|type, path: str) -> list[str]:
        controller = self.get_controller(decider)
        root_path = controller.resource_folder()
        path = self._inner_path(controller, path)
        return (Query
                .folder(path,'**/*')
                .where(lambda z: z.is_file())
                .select(lambda z: str(z.relative_to(root_path)))
                .to_list()
                )

    @endpoint(url='/resources/delete')
    def delete_resource(self, decider: str|type, path: str, ignore_errors: bool = False):
        controller = self.get_controller(decider)
        path = self._inner_path(controller, path)
        if path.is_file():
            os.unlink(path)
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            if not ignore_errors:
                raise ValueError(f"Cannot delete {path} of decider {controller.get_name()}: no such file/folder")

    @endpoint(url="/resources/setup", method='POST')
    def setup(self, setup: ControllersSetup):
        from .setuper import Setuper
        setuper = Setuper(setup, self)
        setuper.make_all()

    @endpoint(url='/resources/download_models', method='POST')
    def download_models(self, decider: str|type, models: list):
        controller = self.get_controller(decider)
        if not isinstance(controller, IModelDownloadingController):
            raise ValueError(f"Decider {decider} is not ModelDownloadingController")
        controller.download_models(models)



