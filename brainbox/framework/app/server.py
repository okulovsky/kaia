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
from brainbox.framework.common import Loc, Locator
from brainbox.framework.controllers.architecture import ControllerRegistry
from foundation_kaia.marshalling_2.marshalling.server.components import ServiceComponent
from foundation_kaia.marshalling_2 import StaticFilesComponent, IServer, WebAppEntryPoint

from .batches.service import BatchesService
from .diagnostics.service import DiagnosticsService
from .jobs.service import JobsService
from .tasks.service import TasksService
from .controllers.service import ControllersService
from .deciders.service import DeciderService
from foundation_kaia.marshalling_2.amenities import Storage
from brainbox.framework.common.streaming import StreamingStorage


@dataclass
class BrainBoxServerSettings:
    registry: ControllerRegistry
    planner: IPlanner = field(default_factory=SimplePlanner)
    port: int = 18090
    debug_output: bool = False
    locator: Locator = field(default_factory=lambda: Loc)
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
    decider: DeciderService


class BrainBoxServer(IServer):
    def __init__(self, settings: BrainBoxServerSettings):
        self.settings = settings


    @staticmethod
    def create_services(settings: BrainBoxServerSettings) -> BrainBoxServices:
        from .api import BrainBoxApi
        engine = create_engine(
            'sqlite:///' + str(settings.locator.db_path),
            connect_args={"check_same_thread": False, "timeout": 15}
        )
        BrainBoxBase.metadata.create_all(engine)
        core = Core(engine, settings.registry, settings.locator, settings.debug_output)
        loop = MainLoop(core, settings.planner, core.command_queue, settings.stop_controllers_at_termination)
        return BrainBoxServices(
            engine=engine,
            command_queue=core.command_queue,
            loop=loop,
            tasks=TasksService(engine, core.command_queue),
            diagnostics=DiagnosticsService(engine, settings.locator.cache_folder, loop),
            controllers=ControllersService(settings.registry, BrainBoxApi(f'127.0.0.1:{settings.port}')),
            cache=Storage(settings.locator.cache_folder),
            streaming_cache=StreamingStorage(settings.locator.cache_folder),
            resources=Storage(settings.locator.resources_folder),
            batches=BatchesService(engine, core.command_queue),
            jobs = JobsService(engine, core.command_queue),
            decider = DeciderService(settings.registry),
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

        ServiceComponent(services.jobs).mount(app)
        ServiceComponent(services.batches).mount(app)
        ServiceComponent(services.tasks).mount(app)
        ServiceComponent(services.diagnostics).mount(app)
        ServiceComponent(services.controllers).mount(app)
        ServiceComponent(services.decider).mount(app)
        ServiceComponent(services.cache, 'cache').mount(app)
        ServiceComponent(services.streaming_cache, 'streaming-cache').mount(app)
        ServiceComponent(services.resources, 'resources').mount(app)


        StaticFilesComponent(Path(__file__).parent / 'static').mount(app)

        return app

    def get_port(self) -> int:
        return self.settings.port

    def create_web_app_entry_point(self) -> WebAppEntryPoint:
        return WebAppEntryPoint(self._create_app(), self.settings.port, daemon_threads=(self.loop.run,))
