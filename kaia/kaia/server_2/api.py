import time
import uuid

from .bus import Bus, BusItem
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from .server import KaiaServerSettings, KaiaServer
from kaia.infra.app import KaiaApp
import requests
import webbrowser
from kaia.eaglesong.core import primitives
from pathlib import Path
from kaia.infra import Loc, FileIO
from ..core import KaiaMessage


@dataclass
class Message:
    class Type(Enum):
        ToUser = 0
        FromUser = 1
        System = 2
        Error = 3

    type: 'Message.Type'
    text: str
    sender: str|None = None
    avatar: str|None = None


class KaiaApi:
    def __init__(self,
                 bus: Bus,
                 session_id: str,
                 last_message_id: int|None = None,
                 cache_folder: Path|None = None
                 ):
        self.bus = bus
        self.session_id = session_id
        self.last_message_id: int|None = last_message_id
        self.cache_folder = cache_folder if cache_folder is not None else Loc.temp_folder/'kaia_api_cache'

    def add_image(self, image: str|primitives.Image):
        if isinstance(image, primitives.Image):
            FileIO.write_bytes(image.data, self.cache_folder/image.id)
            image = image.id

        self.bus.add_message(BusItem(
            session_id = self.session_id,
            timestamp = datetime.now(),
            type = "reaction_image",
            payload = dict(filename=image)
        ))

    def add_sound(self, sound: str|primitives.Audio):
        if isinstance(sound, primitives.Audio):
            if sound.id is None:
                sound.id = str(uuid.uuid4())+'.wav'
            FileIO.write_bytes(sound.data, self.cache_folder/sound.id)
            sound = sound.id

        self.bus.add_message(BusItem(
            session_id = self.session_id,
            timestamp = datetime.now(),
            type = "reaction_audio",
            payload = dict(filename=sound)
        ))

    def add_message(self, message: Message|KaiaMessage):
        if isinstance(message, KaiaMessage):
            message = Message(
                Message.Type.Error if message.is_error else (Message.Type.ToUser if message.is_bot else Message.Type.FromUser),
                message.text,
                message.speaker,
                message.avatar
            )
        self.bus.add_message(BusItem(
            session_id = self.session_id,
            timestamp = datetime.now(),
            type = 'reaction_message',
            payload = dict(
                type = message.type.name,
                text = message.text,
                sender = message.sender,
                avatar = message.avatar
            )))

    def pull_updates(self):
        updates = self.bus.get_messages(self.session_id, self.last_message_id)
        for update in updates:
            self.last_message_id = update.id
        return updates


    class Test:
        def __init__(self,
                     settings: KaiaServerSettings,
                     custom_session_id: str|None = None
                     ):
            self.settings = settings
            self.custom_session_id = custom_session_id
            self.app: KaiaApp|None = None

        def __enter__(self):
            self.app = KaiaApp()
            service = KaiaServer(self.settings)
            self.app.add_subproc_service(service)
            self.app.run_services_only()

            ok = False
            for i in range(100):
                try:
                    reply = requests.get(f'http://127.0.0.1:{self.settings.port}/heartbit')
                    if reply.status_code == 200:
                        ok = True
                        break
                except:
                    pass
                time.sleep(0.1)

            if not ok:
                raise ValueError("Could not wait for the service to start")

            bus = Bus(self.settings.db_path)
            current_sessions = bus.get_sessions()

            webbrowser.open(f'http://127.0.0.1:{self.settings.port}/')
            new_session = None
            for i in range(100):
                new_sessions = bus.get_sessions()
                
                if len(new_sessions) > len(current_sessions):
                    new_session = [s for s in new_sessions if s not in current_sessions][0]
                    break
                time.sleep(0.1)

            if new_session is None:
                raise ValueError("Could not wait until the browser creates a session")

            api = KaiaApi(bus, new_session)
            return api

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.app.exit()




