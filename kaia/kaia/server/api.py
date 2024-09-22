import json
import os
import time

from kaia.infra import MarshallingEndpoint
from .bus import Bus, BusItem
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from .server import KaiaServerSettings, KaiaServer
from kaia.infra.app import KaiaApp
import requests



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
    def __init__(self, bus: Bus, session_id: str):
        self.bus = bus
        self.session_id = session_id

    def add_image(self, image: str):
        self.bus.add_message(BusItem(
            session_id = self.session_id,
            timestamp = datetime.now(),
            type = "reaction_image",
            payload = json.dumps(image)
        ))

    def add_sound(self, sound: str):
        self.bus.add_message(BusItem(
            session_id = self.session_id,
            timestamp = datetime.now(),
            type = "reaction_audio",
            payload = json.dumps(sound)
        ))

    def add_message(self, message: Message):
        self.bus.add_message(BusItem(
            session_id = self.session_id,
            timestamp = datetime.now(),
            type = 'reaction_message',
            payload = json.dumps(dict(
                type = message.type.name,
                text = message.text,
                sender = message.sender,
                avatar = message.avatar
            ))))

    def get_updates(self, last_message_id: int|None = None) -> list[BusItem]:
        return self.bus.get_messages(self.session_id, last_message_id)

    class Test:
        def __init__(self,
                     settings: KaiaServerSettings,
                     browser_command: str = 'firefox',
                     ):
            self.settings = settings
            self.browser_command = browser_command
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
            os.system(f'{self.browser_command} http://127.0.0.1:{self.settings.port}/')

            new_session = None
            for i in range(100):
                new_sessions = bus.get_sessions()
                print(current_sessions, new_sessions)

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




