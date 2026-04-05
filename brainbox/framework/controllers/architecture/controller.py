import pickle
from typing import *
from abc import ABC, abstractmethod
from unittest import TestCase
from ...common import Locator, Loc
from .resource_folder import ResourceFolder
from .controller_context import ControllerContext
from ..self_test import SelfTestCase, logger
from foundation_kaia.logging import HtmlReport


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


    #endregion

    #region Self-test

    def custom_self_test(self, api, tc: TestCase):
        pass

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        return []

    def _run_self_test(self, api, tc: TestCase, locator: Locator):
        output_folder = locator.self_test_path
        html_path = output_folder / (self.get_name() + '.html')
        if str(html_path).startswith('/'):
            html_link = f'file://{html_path}'
        else:
            html_link = f'file:///{html_path}'.replace('\\','/')

        items = []
        error = False
        with logger.with_callback(items.append):
            with HtmlReport(html_path):
                try:
                    for case in self.self_test_cases():
                        result = case.execute(api, tc)
                        title = case.title
                        if title is None:
                            title = f"Test Case: {result.method}:{result.parameter}"
                        with logger.section(title):
                            logger.info(result)

                    self.custom_self_test(api, tc)
                except Exception as ex:
                    error = True
                    logger.error(ex)
                    raise ValueError(f"Exception has occured during self-test. View the report {html_link}") from ex
                finally:
                    with open(output_folder / self.get_name(), 'wb') as f:
                        pickle.dump(items, f)
                    if not error:
                        print(f"Self-test completed successfully. View the report {html_link}")




    def self_test(self,
                  tc: None|TestCase = None,
                  locator: Locator = Loc, #Should use a different locator
                  api = None
                  ):
        if tc is None:
            tc = TestCase()

        from brainbox.framework import BrainBoxApi
        if api is not None:
            if not isinstance(api, BrainBoxApi):
                raise ValueError("Api should be BrainBoxApi")
            else:
                self._run_self_test(api, tc, locator)
                return

        with BrainBoxApi.test(port=18091, locator=locator, run_controllers_in_default_environment=False) as api:
            try:
                self._run_self_test(api, tc, locator)
            finally:
                #Also cancel all, otherwise the task persists in the database and will be executed next time self-test runs
                self.stop_all()







        # endregion