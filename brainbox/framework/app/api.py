from .diagnostics import IDiagnosticsService, DiagnosticsApi
from .tasks import TasksApi, ITasksService
from .controllers import ControllersApi, InternalControllersApi
from .batches import BatchesApi, IBatchesService
from foundation_kaia.marshalling_2.amenities import StorageApi, IStorage, StorageApiWrap
from foundation_kaia.marshalling_2 import TestApi
from foundation_kaia.marshalling_2.marshalling.server.utils import ApiUtils
from brainbox.framework.common.streaming import StreamingStorageApi, IStreamingStorage
from typing import Any, Iterable, Union
from brainbox.framework.task import IJobRequestFactory
from ..controllers import ControllerRegistry, ControllerLike
from ..common import Loc, Locator
import functools


def _make_brainbox_api(url, locator):
    api = BrainBoxApi(url)
    api.locator = locator
    return api


class BrainBoxApi:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.tasks: ITasksService = TasksApi(base_url)
        self.diagnostics: IDiagnosticsService = DiagnosticsApi(base_url)
        self.controllers = ControllersApi(InternalControllersApi(base_url))
        self.batches: IBatchesService = BatchesApi(base_url)
        self.cache: IStorage = StorageApi(base_url, 'cache')
        self.streaming_cache: IStreamingStorage = StreamingStorageApi(base_url, "streaming-cache")
        self._resources_storage = StorageApi(base_url, 'resources')

    def resources(self, controller: ControllerLike) -> IStorage:
        name = ControllerRegistry.to_controller_name(controller)
        return StorageApiWrap(self._resources_storage, name)

    def wait_for_connection(self, time_in_seconds: int = 10) -> None:
        ApiUtils.wait_for_reply(f'{self.base_url}/heartbeat', time_in_seconds)

    @staticmethod
    def serverless_test(services=None, allow_failures: bool = False, planner=None) -> 'ServerlessTest':
        from .serverless_test import ServerlessTest
        from brainbox.framework.controllers.architecture import ControllerRegistry
        registry = ControllerRegistry.discover_or_create(services)
        return ServerlessTest(registry=registry, planner=planner)

    @staticmethod
    def test(services=None,
             run_controllers_in_default_environment: bool = True,
             always_on_planner: bool = False,
             stop_containers_at_termination: bool = True,
             port: int = 18090,
             locator=None,
             ) -> 'TestApi[BrainBoxApi]':
        from .server import BrainBoxServer, BrainBoxServerSettings
        from brainbox.framework.controllers.architecture import ControllerRegistry
        from brainbox.framework.job_processing import AlwaysOnPlanner, SimplePlanner
        registry = ControllerRegistry.discover_or_create(services)
        if not run_controllers_in_default_environment and locator is not None:
            registry.locator = locator
        planner = AlwaysOnPlanner(AlwaysOnPlanner.Mode.FindThenStart) if always_on_planner else SimplePlanner()
        temp_folder = None
        if locator is None:
            temp_folder = Loc.create_test_folder('brainbox_server_test')
            locator = Locator(temp_folder.__enter__())
        settings = BrainBoxServerSettings(
            registry=registry,
            planner=planner,
            port=port,
            locator=locator,
            stop_controllers_at_termination=stop_containers_at_termination
        )
        on_exit = functools.partial(temp_folder.__exit__, None, None, None) if temp_folder is not None else None
        return TestApi(
            functools.partial(_make_brainbox_api, locator=locator),
            BrainBoxServer(settings),
            on_exit=on_exit
        )


    def add(self, task: Any) -> str|list[str]:
        if isinstance(task, IJobRequestFactory):
            request_stack = [task.to_job_request()]
        else:
            request_stack = []
            for index, e in enumerate(task):
                if isinstance(e, IJobRequestFactory):
                    request_stack.append(e.to_job_request())
                else:
                    raise ValueError(f"Expected IJobRequestFactory, but at index {index} was {e}")

        all_jobs = []
        resulting_ids = []
        for stack in request_stack:
            for job in stack.jobs:
                if job.batch is None:
                    job.batch = stack.main_id
            resulting_ids.append(stack.main_id)
            all_jobs.extend(stack.jobs)

        self.tasks.base_add(list(reversed(all_jobs)))
        if len(request_stack) == 1:
            return resulting_ids[0]
        else:
            return resulting_ids

    def join(self, task: Union[str, Iterable[str]]):
        if isinstance(task, str):
            ids = [task]
            not_list = True
        else:
            try:
                ids = list(task)
            except:
                raise ValueError(f"Task is expected to be str (job id), IBrainBoxTask or Iterable, but was {task}")
            not_list = False
        result = self.tasks.base_join(ids)
        if not_list:
            return result[0]
        return result

    def execute(self, task: Any) -> Any:
        ids = self.add(task)
        return self.join(ids)

    def last_call(self):
        return self.diagnostics.last_call()

