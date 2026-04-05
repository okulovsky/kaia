import os
import pickle
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from threading import Thread

from brainbox.framework.common import FileIO
from brainbox.framework.controllers.architecture import ControllerRegistry
from brainbox.framework.controllers.docker_web_service_controller import DockerWebServiceApi
from foundation_kaia.brainbox_utils import IModelLoadingSupport
from foundation_kaia.logging import Logger
from foundation_kaia.logging.simple import ExceptionItem

from .dto import (
    LogItem, InstallationReport, ControllerInstance, ControllerStatus,
    ControllersStatus, SelfTestResult, ControllersSetup,
)
from .interface import IControllersService
from .logging import LoggingLocalExecutor, LoggingApiCallback


def _log_to_items(captured: list) -> list[LogItem]:
    return [LogItem(timestamp=ts, data=item.to_string()) for ts, item in captured]


@dataclass
class RunningInstallation:
    report: InstallationReport
    controller: object
    thread: Thread | None = None
    _captured: list = field(default_factory=list)
    _callback: object = None

    def run(self):
        try:
            self.controller.install()
        except:
            self.report.error = traceback.format_exc()
        finally:
            if self._callback is not None and self._callback in Logger.ON_ITEM:
                Logger.ON_ITEM.remove(self._callback)

    def exited(self):
        return not self.thread.is_alive()


class ControllersService(IControllersService):
    def __init__(self, registry: ControllerRegistry, api=None):
        self.registry = registry
        self.api = api
        self.running_installation: RunningInstallation | None = None

    def _get_controller(self, decider: str):
        name = ControllerRegistry.to_controller_name(decider)
        return self.registry.get_controller(name)

    def status(self) -> ControllersStatus:
        installation_statuses = self.registry.get_installation_statuses()
        controllers = []

        for name, installation_status in installation_statuses.items():
            if not installation_status.installed or installation_status.dockerless_controller:
                controllers.append(ControllerStatus(
                    name=name,
                    installed=installation_status.installed,
                    dockerless=installation_status.dockerless_controller,
                    size=installation_status.size,
                    has_self_test_report=False,
                    has_errors_in_self_test_report=False,
                    instances=[],
                ))
                continue

            controller = self._get_controller(name)
            instances = []
            for instance_id, parameter in controller.get_running_instances_id_to_parameter().items():
                address = None
                api = controller.find_api(instance_id)
                if isinstance(api, DockerWebServiceApi):
                    address = api.address
                instances.append(ControllerInstance(
                    instance_id=instance_id,
                    parameter=parameter,
                    address=address,
                ))

            report_path = self.registry.locator.self_test_path / name
            has_report = report_path.is_file()
            has_errors = False
            if has_report:
                try:
                    items = FileIO.read_pickle(report_path)
                    if any(isinstance(item, ExceptionItem) for item in items):
                        has_errors = True
                except:
                    pass

            controllers.append(ControllerStatus(
                name=name,
                installed=installation_status.installed,
                dockerless=installation_status.dockerless_controller,
                size=installation_status.size,
                has_self_test_report=has_report,
                has_errors_in_self_test_report=has_errors,
                instances=instances,
            ))

        currently_installing = None
        if self.running_installation is not None and not self.running_installation.exited():
            currently_installing = self.running_installation.report.name

        return ControllersStatus(
            controllers=controllers,
            currently_installing=currently_installing,
        )

    def install(self, decider: str, join: bool | None = None) -> InstallationReport | None:
        if self.running_installation is not None and not self.running_installation.exited():
            raise ValueError("Another installation is in progress")
        self.running_installation = None

        controller = self._get_controller(decider)
        controller.context._executor = LoggingLocalExecutor()
        controller.context._api_callback = LoggingApiCallback()

        installation = RunningInstallation(
            report=InstallationReport(name=controller.get_name(), log=[]),
            controller=controller,
        )

        def on_item(item):
            installation._captured.append((datetime.now(), item))
        installation._callback = on_item
        Logger.ON_ITEM.append(on_item)

        installation.thread = Thread(target=installation.run)
        installation.thread.start()
        self.running_installation = installation

        should_join = join if join is not None else True
        if should_join:
            return self.join_installation()
        return None

    def uninstall(self, decider: str, purge: bool | None = None) -> None:
        self._get_controller(decider).uninstall(purge or False)

    def run(self, decider: str, parameter: str | None = None) -> str:
        if parameter == '':
            parameter = None
        return self._get_controller(decider).run(parameter)

    def stop(self, decider: str, instance_id: str) -> None:
        self._get_controller(decider).stop(instance_id)

    def join_installation(self) -> InstallationReport:
        if self.running_installation is None:
            raise ValueError("No installation is in progress")
        if not self.running_installation.exited():
            self.running_installation.thread.join()

        result = self.running_installation
        self.running_installation = None

        result.report.log = _log_to_items(result._captured)
        if result.report.error is not None:
            raise ValueError(f"Installation threw an exception\n{result.report.error}")
        return result.report

    def installation_report(self) -> InstallationReport:
        if self.running_installation is None:
            raise ValueError("No installation is in progress")
        report = self.running_installation.report
        report.log = _log_to_items(self.running_installation._captured)
        return report

    def self_test(self, decider: str) -> SelfTestResult:
        controller = self._get_controller(decider)
        name = controller.get_name()
        try:
            controller.self_test(
                locator=self.registry.locator,
                api=self.api,
            )
            report_path = self.registry.locator.self_test_path / name
            with open(report_path, 'rb') as f:
                items = pickle.load(f)
            sections = [item.to_html() for item in items]
            return SelfTestResult(name=name, sections=sections)
        except Exception:
            error = traceback.format_exc()
            return SelfTestResult(name=name, error=error, sections=[])

    def delete_self_test(self, decider: str) -> None:
        controller = self._get_controller(decider)
        path = self.registry.locator.self_test_path / controller.get_name()
        if path.is_file():
            os.unlink(path)

    def setup(self, setup: ControllersSetup) -> None:
        for decider in setup.simple_deciders:
            controller = self._get_controller(decider)
            if not controller.get_running_instances_id_to_parameter():
                self.run(decider)

        for decider, parameter in setup.deciders_with_parameters.items():
            controller = self._get_controller(decider)
            running = controller.get_running_instances_id_to_parameter()
            if parameter not in running.values():
                self.run(decider, parameter)

        for decider, model in setup.deciders_with_model.items():
            controller = self._get_controller(decider)
            running = controller.get_running_instances_id_to_parameter()
            if not running:
                self.run(decider)
                running = controller.get_running_instances_id_to_parameter()
            instance_id = next(iter(running))
            api = controller.find_api(instance_id)
            if isinstance(api, IModelLoadingSupport):
                api.load_model(model)


