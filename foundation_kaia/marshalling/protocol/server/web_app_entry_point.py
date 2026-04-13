from dataclasses import dataclass, field
from threading import Thread
from typing import Callable
from fastapi import FastAPI
import uvicorn


@dataclass
class WebAppEntryPoint:
    app: FastAPI
    port: int
    host: str = '0.0.0.0'
    daemon_threads: tuple[Callable, ...] = field(default_factory=tuple)

    def run(self):
        for callable in self.daemon_threads:
            Thread(target=callable, daemon=True).start()
        uvicorn.run(self.app, host=self.host, port=self.port, log_level='warning')
