from dataclasses import dataclass
from flask import Flask

def _mock_serve(app: Flask, host, port, threads):
    app.run(host, port)

@dataclass
class WebAppEntryPoint:
    app: Flask
    port: int
    host: str = '0.0.0.0'
    threads: int = 16

    def run(self):
        try:
            from waitress import serve  # type: ignore
            print(f"Running waitress server at http://{self.host}:{self.port}", flush=True)
        except ModuleNotFoundError:
            print("No waitress server available, running development server", flush=True)
            serve = _mock_serve
        serve(
            self.app,
            host=self.host,
            port=self.port,
            threads=self.threads,
        )
