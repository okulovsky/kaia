from __future__ import annotations

import os

from .diagnostics import IDiagnosticsService, DiagnosticsApi
from .tasks import TasksApi, ITasksService
from .controllers import ControllersApi
from .batches import BatchesApi, IBatchesService
from foundation_kaia.marshalling import StorageApi, IStorage, StorageApiWrap, TestApi, ApiUtils
from brainbox.framework.common.streaming import StreamingStorageApi, IStreamingStorage
from brainbox.framework.common import BrainBoxLocations
from typing import Any, Iterable, Union
from brainbox.framework.task import IJobRequestFactory
from ..controllers import ControllerRegistry, ControllerLike
import functools
from pathlib import Path
from foundation_kaia.misc import Loc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .serverless_test import ServerlessTest


def _make_brainbox_api(url, locations, resources_folder):
    api = BrainBoxApi(url)
    api.debug_locations = locations
    api.debug_resources_folder = resources_folder
    return api


class BrainBoxApi:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.tasks: ITasksService = TasksApi(base_url)
        self.diagnostics: IDiagnosticsService = DiagnosticsApi(base_url)
        self.controllers = ControllersApi(base_url)
        self.batches: IBatchesService = BatchesApi(base_url)
        self.cache: IStorage = StorageApi(base_url, 'cache')
        self.streaming_cache: IStreamingStorage = StreamingStorageApi(base_url, "streaming-cache")
        self._resources_storage = StorageApi(base_url, 'resources')
        self.debug_locations: BrainBoxLocations|None = None
        self.debug_resources_folder: Path|None = None

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
             default_resources_folder: bool = True,
             always_on_planner: bool = False,
             stop_containers_at_termination: bool = True,
             port: int = 18090,
             working_folder: Path|None = None,
             ) -> 'TestApi[BrainBoxApi]':
        from .server import BrainBoxServer, BrainBoxServerSettings
        from brainbox.framework.controllers.architecture import ControllerRegistry
        from brainbox.framework.job_processing import AlwaysOnPlanner, SimplePlanner
        resources_folder = None
        if not default_resources_folder and working_folder is not None:
            resources_folder = working_folder/'resources'
            os.makedirs(resources_folder, exist_ok=True)
        registry = ControllerRegistry.discover_or_create(services, resources_folder)
        planner = AlwaysOnPlanner(AlwaysOnPlanner.Mode.FindThenStart) if always_on_planner else SimplePlanner()

        on_exit = None
        if working_folder is None:
            working_folder_factory = Loc.create_test_folder('brainbox_server_test')
            working_folder = working_folder_factory.__enter__()
            on_exit = functools.partial(working_folder_factory.__exit__, None, None, None)

        locations = BrainBoxLocations.default(working_folder)

        settings = BrainBoxServerSettings(
            registry=registry,
            locations = locations,
            planner=planner,
            port=port,
            stop_controllers_at_termination=stop_containers_at_termination
        )

        return TestApi(
            functools.partial(_make_brainbox_api, locations=locations, resources_folder=resources_folder),
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

