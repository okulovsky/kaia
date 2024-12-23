import pickle
import traceback
from typing import *
from abc import ABC, abstractmethod
from unittest import TestCase
from .test_report import TestReport
from ...common import Loc
from .resource_folder import ResourceFolder
from .controller_context import ControllerContext
from dataclasses import dataclass
import re
from .self_test_report_page import create_self_test_report_page


TSettings = TypeVar("TSettings")


class IController(ABC, Generic[TSettings]):
    # region Abstract methods

    @abstractmethod
    def get_default_settings(self) -> TSettings:
        pass

    @abstractmethod
    def install(self):
        pass

    @abstractmethod
    def uninstall(self, purge: bool = False):
        pass

    class DockerlessInstallation:
        pass

    @abstractmethod
    def find_self_in_list(self, all_images_installed: tuple[str,...]) -> Union[str, None, 'IController.DockerlessInstallation']:
        pass



    @abstractmethod
    def run(self, parameter: str|None) -> str:
        pass

    @abstractmethod
    def stop(self, instance_id: str):
        pass


    @abstractmethod
    def get_running_instances_id_to_parameter(self) -> dict[str, str|None]:
        pass

    @abstractmethod
    def find_api(self, instance_id: str):
        pass

    @abstractmethod
    def _self_test_internal(self, api, tc: TestCase) -> Iterable[TestReport.Item]:
        pass


    #endregion
    # region Context properties

    @property
    def context(self) -> ControllerContext[TSettings]:
        if not hasattr(self, '_context'):
            self._context = ControllerContext(self.get_name(), self.get_default_settings())
        return self._context

    @property
    def resource_folder(self) -> ResourceFolder:
        return self.context.resource_folder


    @property
    def settings(self) -> TSettings:
        return self.context.settings

    # endregion

    # region Convenience methods
    def is_installed(self):
        from .controller_registry import ControllerRegistry
        registry = ControllerRegistry([self])
        status = registry.get_installation_statuses()[self.get_name()]
        return status.installed


    def get_name(self):
        from .controller_registry import ControllerRegistry
        return ControllerRegistry.to_controller_name(type(self))


    def get_snake_case_name(self):
        name = self.get_name()
        result = []
        for i, c in enumerate(name):
            if c.islower():
                result.append(c)
                continue
            if i > 0 and name[i-1].islower():
                result.append('_')
            result.append(c.lower())
        return ''.join(result)


    def is_running(self, parameter: str|None):
        return parameter in self.get_running_instances_id_to_parameter().values()

    def is_any_running(self):
        return len(self.get_running_instances_id_to_parameter()) != 0

    def reinstall(self, purge: bool = False):
        if self.is_installed():
            self.uninstall(purge)
        self.install()

    def stop_all(self):
        for instance_id in self.get_running_instances_id_to_parameter():
            self.stop(instance_id)

    def self_test(self, tc: None|TestCase = None) -> TestReport:
        if tc is None:
            tc = TestCase()
        html_path = Loc.self_test_path / (self.get_name()+'.html')

        from brainbox.framework import BrainBoxApi
        with BrainBoxApi.Test() as api:
            items = []
            error = None
            try:
                for item in self._self_test_internal(api, tc):
                    items.append(item)
            except Exception as ex:
                error = traceback.format_exc()
                raise ValueError(f"Exception has occured during self-test. View the report file://{html_path}") from ex
            finally:
                self.stop_all()
                report = TestReport(self.get_name(), items, error)
                with open(Loc.self_test_path / self.get_name(), 'wb') as file:
                    pickle.dump(report, file)
                with open(html_path, 'w') as file:
                    file.write(create_self_test_report_page(report))

            if error is None:
                print(f"SELF-TEST EXITED SUCCESSFULLY. Report file://{html_path}")
            return report

    # endregion