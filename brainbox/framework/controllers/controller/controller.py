import pickle
import traceback
from typing import *
from abc import ABC, abstractmethod
from unittest import TestCase
from ...common import Locator, Loc
from .resource_folder import ResourceFolder
from .controller_context import ControllerContext
from .test_report import create_self_test_report_page, TestReport
from yo_fluq import FileIO


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
    def _self_test_internal(self, api, tc: TestCase) -> Iterable:
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

    def _run_self_test(self, api, tc: TestCase, locator: Locator):
        output_folder = locator.self_test_path
        html_path = output_folder / (self.get_name() + '.html')
        if str(html_path).startswith('/'):
            html_link = f'file://{html_path}'
        else:
            html_link = f'file:///{html_path}'.replace('\\','/')
        items = []
        error = None
        try:
            for item in self._self_test_internal(api, tc):
                items.append(item)
        except Exception as ex:
            error = traceback.format_exc()
            raise ValueError(f"Exception has occured during self-test. View the report {html_link}") from ex
        finally:
            report = TestReport(self.get_name(), items, error, type(self))
            FileIO.write_pickle(report, output_folder/self.get_name())
            FileIO.write_text(create_self_test_report_page(report), html_path)
        if error is None:
            print(f"SELF-TEST EXITED SUCCESSFULLY. Report {html_link}")
        return report


    def self_test(self,
                  tc: None|TestCase = None,
                  locator: Locator = Loc,
                  api = None
                  ) -> TestReport:
        if tc is None:
            tc = TestCase()

        from brainbox.framework import BrainBoxApi
        if api is not None:
            if not isinstance(api, BrainBoxApi):
                raise ValueError("Api should be BrainBoxApi")
            else:
                return self._run_self_test(api, tc, locator)

        with BrainBoxApi.Test(port=18091, locator=locator, run_controllers_in_default_environment=False) as api:
            try:
                result = self._run_self_test(api, tc, locator)
                return result
            finally:
                self.stop_all()







    # endregion