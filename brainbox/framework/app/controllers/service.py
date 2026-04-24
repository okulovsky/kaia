import os
import pickle
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from threading import Thread

from brainbox.framework.common import FileIO
from brainbox.framework.common.decider_model import DeciderModel
from brainbox.framework.controllers.architecture import ControllerRegistry, ControllerOverDecider
from brainbox.framework.controllers.docker_web_service_controller import DockerWebServiceApi
from foundation_kaia.brainbox_utils import IModelLoadingSupport
from foundation_kaia.logging import Logger
from foundation_kaia.logging.simple import ExceptionItem
from foundation_kaia.marshalling import SERVICE_ATTR
from foundation_kaia.marshalling.reflector import DeclaredType
from foundation_kaia.marshalling.documenter import ServiceDocumentation
from foundation_kaia.marshalling.amenities.documentation_service.html_helper import build_snippet

from .dto import (
    LogItem, InstallationReport, ControllerInstance, ControllerStatus,
    ControllersStatus, SelfTestResult, ControllersSetup,
    SelfTestCaseDocumentation, MethodExamples, ControllerExamples,
)
from .interface import IControllersService
from .logging import LoggingLocalExecutor, LoggingApiCallback
from pathlib import Path

class ControllersService(IControllersService):
    def __init__(self, registry: ControllerRegistry, self_test_folder: Path, api=None):
        self.registry = registry
        self.self_test_folder = self_test_folder
        self.api = api

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
                base_url = None
                api = controller.find_api(instance_id)
                if isinstance(api, DockerWebServiceApi):
                    base_url = api.base_url
                instances.append(ControllerInstance(
                    instance_id=instance_id,
                    parameter=parameter,
                    base_url = base_url,
                ))

            report_path = self.self_test_folder / name
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

        return ControllersStatus(
            controllers=controllers,
        )


    def uninstall(self, decider: str, purge: bool | None = None) -> None:
        self._get_controller(decider).uninstall(purge or False)

    def run(self, decider: str, parameter: str | None = None) -> str:
        if parameter == '':
            parameter = None
        return self._get_controller(decider).run(parameter)

    def stop(self, decider: str, instance_id: str) -> None:
        self._get_controller(decider).stop(instance_id)

    def self_test(self, decider: str) -> SelfTestResult:
        controller = self._get_controller(decider)
        name = controller.get_name()
        try:
            controller.self_test(
                self_test_folder=self.self_test_folder,
                api=self.api,
            )
            report_path = self.self_test_folder / name
            with open(report_path, 'rb') as f:
                items = pickle.load(f)
            sections = [item.to_html() for item in items]
            return SelfTestResult(name=name, sections=sections)
        except Exception:
            error = traceback.format_exc()
            return SelfTestResult(name=name, error=error, sections=[])

    def self_test_report(self, decider: str) -> str:
        controller = self._get_controller(decider)
        path = self.self_test_folder / controller.get_name()
        with open(path, 'rb') as f:
            items = pickle.load(f)
        return '\n'.join(item.to_html() for item in items)

    def delete_self_test(self, decider: str) -> None:
        controller = self._get_controller(decider)
        path = self.self_test_folder / controller.get_name()
        if path.is_file():
            os.unlink(path)

    def documentation(self, name: str) -> list[ServiceDocumentation]:
        controller = self._get_controller(name)
        if isinstance(controller, ControllerOverDecider):
            return []
        api_class = self.registry.get_api_class(name)
        if api_class is None:
            return []
        dt = DeclaredType.parse(api_class)
        result = []
        for mro_elem in dt.mro:
            if SERVICE_ATTR not in mro_elem.type.__dict__:
                continue
            tp = mro_elem.generic_type or mro_elem.type
            result.append(ServiceDocumentation.parse(tp))
        return result

    def documentation_html(self, name: str) -> bytes:
        docs = self.documentation(name)
        return build_snippet(docs).encode('utf-8')

    def examples(self, name: str) -> ControllerExamples:
        api_class = self.registry.get_api_class(name)
        controller = self.registry.get_controller(name)
        if api_class is None:
            return ControllerExamples(name=name, docstring=None, methods=[])

        self_test_cases = list(controller.self_test_cases())
        decider_model = DeciderModel.parse(api_class)

        methods = []
        for dm in decider_model.methods.values():
            method_cases = []
            for case in self_test_cases:
                job_request = case.task.to_job_request()
                if len(job_request.jobs) != 1:
                    continue
                job = job_request.jobs[0]
                if job.method != dm.method_name:
                    continue
                method_cases.append(SelfTestCaseDocumentation(
                    title=case.title,
                    method=dm.method_name,
                    arguments=job.arguments,
                ))
            methods.append(MethodExamples(
                method_name=dm.method_name,
                self_test_cases=method_cases,
                is_file=list(dm.file_argument_names),
                result_is_file=dm.result_is_file,
            ))

        return ControllerExamples(
            name=name,
            docstring=api_class.__doc__,
            methods=methods,
        )

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


