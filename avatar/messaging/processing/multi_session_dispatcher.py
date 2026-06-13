import threading
import time
from threading import Thread
from time import monotonic
from typing import Callable
from foundation_kaia.marshalling import TypeTools
from ..core import IMessageRepository
from dataclasses import dataclass

@dataclass
class SessionProcessingData:
    session: str
    stop_flag: threading.Event
    last_activity: float
    thread: threading.Thread|None = None




class MultiSessionDispatcher:
    def __init__(self,
                 repo: IMessageRepository,
                 factory: Callable[[SessionProcessingData], Callable],
                 kill_inactive_sessions_after_in_seconds: float | None = None,
                 ):
        self._repo = repo
        self._factory = factory
        self._kill_inactive = kill_inactive_sessions_after_in_seconds
        self._sessions: dict[str, SessionProcessingData] = {}
        self._stop_flag = threading.Event()

    def stop(self):
        self._stop_flag.set()
        for data in self._sessions.values():
            data.stop_flag.set()

    def _start_session(self, session: str):
        data = SessionProcessingData(
            session,
            threading.Event(),
            time.monotonic(),
        )
        target = self._factory(data)
        data.thread = Thread(target=target, daemon=True)
        self._sessions[session] = data
        data.thread.start()

    def _kill_session(self, session: str):
        data = self._sessions[session]
        data.stop_flag.set()
        del self._sessions[session]

    def run(self):
        self._repo.wait_for_availability()
        while not self._stop_flag.is_set():
            result = self._repo.get(None, self._last_id, timeout_in_seconds=1)
            for element in result.messages:
                self._last_id = element.message.envelop.id
                session = element.session
                if session in self._sessions:
                    self._sessions[session].last_activity = time.monotonic()
                else:
                    self._start_session(session)

            if self._kill_inactive is not None:
                now = monotonic()
                inactive = [s for s in self._sessions.values() if s.last_activity - now > self._kill_inactive]
                for session in inactive:
                    self._kill_session(session.session)


    def run_in_thread(self):
        Thread(target=self.run, daemon=True).start()
