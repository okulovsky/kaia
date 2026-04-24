import uvicorn
from dataclasses import dataclass, field
from pathlib import Path
from threading import Thread
from typing import Any

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, PlainTextResponse
from sqlalchemy import create_engine

from brainbox.framework.job_processing import IPlanner, MainLoop, Core, SimplePlanner
from brainbox.framework.job_processing.main_loop import CommandQueue
from brainbox.framework.job_processing.core.job import BrainBoxBase
from brainbox.framework.common import BrainBoxLocations
from brainbox.framework.controllers.architecture import ControllerRegistry
from foundation_kaia.marshalling import ServiceComponent, StaticFilesComponent, IServer, WebAppEntryPoint
from foundation_kaia.marshalling.amenities import DocumentationService

from .batches.service import BatchesService
from .diagnostics.service import DiagnosticsService
from .jobs.service import JobsService
from .tasks.service import TasksService
from .controllers.service import ControllersService
from .controllers.side_process import SideProcessService, InstallationSideProcess, SelfTestSideProcess, SideProcessPool
from foundation_kaia.marshalling.amenities import Storage
from brainbox.framework.common.streaming import StreamingStorage
from foundation_kaia.misc import Loc

@dataclass
class BrainBoxServerSettings:
    registry: ControllerRegistry
    locations: BrainBoxLocations
    planner: IPlanner = field(default_factory=SimplePlanner)
    port: int = 18090
    debug_output: bool = False
    stop_controllers_at_termination: bool = True


@dataclass
class BrainBoxServices:
    engine: Any
    command_queue: CommandQueue
    loop: MainLoop
    tasks: TasksService
    diagnostics: DiagnosticsService
    controllers: ControllersService
    cache: Storage
    streaming_cache: StreamingStorage
    resources: Storage
    batches: BatchesService
    jobs: JobsService
    install_side_process: SideProcessService
    self_test_side_process: SideProcessService


class BrainBoxServer(IServer):
    def __init__(self, settings: BrainBoxServerSettings):
        self.settings = settings


    @staticmethod
    def create_services(settings: BrainBoxServerSettings) -> BrainBoxServices:
        from .api import BrainBoxApi
        engine = create_engine(
            'sqlite:///' + str(settings.locations.db_path),
            connect_args={"check_same_thread": False, "timeout": 15}
        )
        BrainBoxBase.metadata.create_all(engine)
        core = Core(engine, settings.registry, settings.locations.cache_folder, settings.debug_output)
        loop = MainLoop(core, settings.planner, core.command_queue, settings.stop_controllers_at_termination)
        api = BrainBoxApi(f'http://127.0.0.1:{settings.port}')
        pool = SideProcessPool()
        return BrainBoxServices(
            engine=engine,
            command_queue=core.command_queue,
            loop=loop,
            tasks=TasksService(engine, core.command_queue),
            diagnostics=DiagnosticsService(engine, settings.locations.cache_folder, loop),
            controllers=ControllersService(settings.registry, settings.locations.self_test_folder, api),
            cache=Storage(settings.locations.cache_folder),
            streaming_cache=StreamingStorage(settings.locations.cache_folder),
            resources=Storage(settings.registry.resources_folder),
            batches=BatchesService(engine, core.command_queue),
            jobs=JobsService(engine, core.command_queue),
            install_side_process=SideProcessService(
                pool,
                lambda decider: InstallationSideProcess(settings.registry.get_controller(decider))
            ),
            self_test_side_process=SideProcessService(
                pool,
                lambda decider: SelfTestSideProcess(settings.registry.get_controller(decider), settings.locations.self_test_folder, api)
            ),
        )

    def _create_app(self) -> FastAPI:
        services = BrainBoxServer.create_services(self.settings)
        self.loop = services.loop

        app = FastAPI()

        @app.get('/')
        def root():
            return RedirectResponse('/static/batches.html')

        @app.get('/heartbeat')
        def heartbeat():
            return PlainTextResponse('OK')

        service_components = [
            ServiceComponent(services.jobs),
            ServiceComponent(services.batches),
            ServiceComponent(services.tasks),
            ServiceComponent(services.diagnostics),
            ServiceComponent(services.controllers),
            ServiceComponent(services.install_side_process, 'controllers-service/install'),
            ServiceComponent(services.self_test_side_process, 'controllers-service/self-test'),
            ServiceComponent(services.cache, 'cache'),
            ServiceComponent(services.streaming_cache, 'streaming-cache'),
            ServiceComponent(services.resources, 'resources'),
        ]
        for sc in service_components:
            sc.mount(app)

        ServiceComponent(DocumentationService(service_components), 'doc').mount(app)

        StaticFilesComponent(Path(__file__).parent / 'static').mount(app)

        return app

    def get_port(self) -> int:
        return self.settings.port

    def create_web_app_entry_point(self) -> WebAppEntryPoint:
        return WebAppEntryPoint(self._create_app(), self.settings.port, daemon_threads=(self.loop.run,))
