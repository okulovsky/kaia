from dataclasses import dataclass, field

from .messages import AvatarMessagingService, create_aliases, AvatarMessageRepository
from ..messaging import AvatarClient, IMessage
from foundation_kaia.marshalling_2.amenities import Storage, StaticFilesComponent
from foundation_kaia.marshalling_2 import ServiceComponent, IServer, WebAppEntryPoint, IComponent
from brainbox.framework.common.streaming import StreamingStorage
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, PlainTextResponse, HTMLResponse
from .audio_dashboard import AudioDashboardComponent

@dataclass
class AvatarServerSettings:
    port: int = 13002
    hide_logs: bool = True
    aliases_discovery_namespaces: tuple[str,...] = ()
    messages_ttl_in_seconds: int = 60*60
    cache_folder: Path|None = None
    web_folder: Path|None = None
    frontend_folder: Path|None = None

    resources_folder: Path|None = None
    extra_components: tuple[IComponent,...] = ()
    custom_html: str|None = None
    custom_aliases: dict[str, type]|None = None
    starting_messages: dict[str, tuple[IMessage,...]]|None = None



class AvatarServer(IServer):
    def __init__(self, settings: AvatarServerSettings):
        self.settings = settings

    def get_port(self) -> int:
        return self.settings.port

    def create_web_app_entry_point(self) -> WebAppEntryPoint:
        service_components = {}

        aliases = create_aliases(self.settings.aliases_discovery_namespaces)
        if self.settings.custom_aliases:
            aliases.update(self.settings.custom_aliases)

        messaging_service = AvatarMessagingService(
            aliases or None,
            self.settings.messages_ttl_in_seconds,
            starting_messages=self.settings.starting_messages,
        )
        service_components['messaging'] = messaging_service

        if self.settings.cache_folder is not None:
            service_components['cache'] = Storage(self.settings.cache_folder)
            service_components['streaming'] = StreamingStorage(self.settings.cache_folder)

        if self.settings.resources_folder is not None:
            service_components['resources'] = Storage(self.settings.resources_folder)

        app = FastAPI()

        @app.middleware('http')
        async def cross_origin_isolation(request, call_next):
            response = await call_next(request)
            response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
            response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
            return response

        @app.get('/')
        def root():
            if self.settings.custom_html is not None:
                return HTMLResponse(self.settings.custom_html)
            if self.settings.web_folder is not None:
                return RedirectResponse('/web/index.html')
            return PlainTextResponse("OK")

        @app.get('/heartbeat')
        def heartbeat():
            return PlainTextResponse('OK')

        for name, component in service_components.items():
            ServiceComponent(component, name).mount(app)

        client = AvatarClient(AvatarMessageRepository(messaging_service), 'default')
        AudioDashboardComponent(client, self.settings.cache_folder).mount(app)

        if self.settings.web_folder is not None:
            StaticFilesComponent(self.settings.web_folder, '/web').mount(app)

        if self.settings.frontend_folder is not None:
            StaticFilesComponent(self.settings.frontend_folder, '/frontend').mount(app)

        for component in self.settings.extra_components:
            component.mount(app)

        return WebAppEntryPoint(
            app,
            self.settings.port,
        )