import subprocess
import sys
import threading
import time
from pathlib import Path
import requests
from interface import ILlamaLoraServer

LLAMA_BINARY = '/app/llama-server'
LLAMA_PORT = 8081
LLAMA_URL = f'http://127.0.0.1:{LLAMA_PORT}'
MODELS_FOLDER = Path('/app/models')
LOADING_TIMEOUT_IN_SECONDS = 300


def _forward(stream, dest):
    for line in stream:
        dest.buffer.write(line)
        dest.buffer.flush()


class LlamaLoraServerService(ILlamaLoraServer):
    """
    Runs llama-server as a subprocess. llama-server loads the adapters only at the start,
    so when an adapter is requested that is not loaded, or its file has changed since it was loaded,
    llama-server is restarted with the adapters currently in the folder.
    """
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.lock = threading.Lock()
        self.process: subprocess.Popen | None = None
        self.taskname2id: dict[str, int] = {}
        self.taskname2mtime: dict[str, float] = {}
        self._restart()

    @property
    def adapters_folder(self) -> Path:
        return MODELS_FOLDER / self.model_id / 'lora_adapters'

    def _adapter_files(self) -> dict[str, Path]:
        if not self.adapters_folder.is_dir():
            return {}
        return {path.stem: path for path in sorted(self.adapters_folder.glob('*.gguf'))}

    def _stop(self):
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process = None

    def _wait_for_boot(self):
        begin = time.monotonic()
        while time.monotonic() - begin < LOADING_TIMEOUT_IN_SECONDS:
            if self.process.poll() is not None:
                raise RuntimeError(f"llama-server exited with the code {self.process.returncode}")
            try:
                if requests.get(f'{LLAMA_URL}/health').status_code == 200:
                    return
            except requests.ConnectionError:
                pass
            time.sleep(0.5)
        raise RuntimeError(f"llama-server did not start in {LOADING_TIMEOUT_IN_SECONDS} seconds")

    def _restart(self):
        self._stop()
        files = self._adapter_files()
        cmd = [
            LLAMA_BINARY,
            '--lora-init-without-apply',
            '--host', '127.0.0.1',
            '--port', str(LLAMA_PORT),
            '--model', str(MODELS_FOLDER / self.model_id / 'model.gguf'),
            '--no-mmproj',
        ]
        for path in files.values():
            cmd.extend(['--lora', str(path)])
        # The shared libraries are next to the binary, and it finds them only from its own folder
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=Path(LLAMA_BINARY).parent)
        threading.Thread(target=_forward, args=(self.process.stdout, sys.stdout), daemon=True).start()
        threading.Thread(target=_forward, args=(self.process.stderr, sys.stderr), daemon=True).start()
        self._wait_for_boot()

        reply = requests.get(f'{LLAMA_URL}/lora-adapters')
        reply.raise_for_status()
        self.taskname2id = {Path(item['path']).stem: item['id'] for item in reply.json()}
        self.taskname2mtime = {name: path.stat().st_mtime for name, path in files.items()}

    def _ensure_loaded(self, task_name: str):
        path = self.adapters_folder / f'{task_name}.gguf'
        if task_name in self.taskname2id:
            if not path.is_file() or path.stat().st_mtime == self.taskname2mtime.get(task_name):
                return
        elif not path.is_file():
            raise ValueError(f"There is no adapter `{task_name}` for the model `{self.model_id}`: {path} is not found")
        self._restart()

    def reload(self) -> None:
        with self.lock:
            self._restart()

    def completion(self, *, task_name: str, prompt: str|None = None, prompts: list[str]|None = None, max_tokens: int = -1) -> str|list[str]:
        if prompt is None and prompts is None:
            raise ValueError("You must provide either `prompt` or `prompts`, none given.")
        if prompt is not None and prompts is not None:
            raise ValueError("You must provide either `prompt` or `prompts`, not both.")

        with self.lock:
            self._ensure_loaded(task_name)
            payload = {
                "prompt": prompt or prompts,
                "n_predict": max_tokens,
                "temperature": 0.0,  # TODO: might need to support later (e.g. for paraphrasing)
                "stream": False,  # TODO: might need to support later (e.g. for paraphrasing)
                "lora": [{"id": self.taskname2id[task_name], "scale": 1.0}],
                "response_fields": ["content"],  # TODO: add "stop" for stream=True
            }
            reply = requests.post(f'{LLAMA_URL}/completion', json=payload)

        if reply.status_code != 200:
            raise ValueError(f'Status code {reply.status_code}, value\n{reply.text}')
        data = reply.json()
        if prompt is not None:
            return data["content"]
        return [item["content"] for item in data]
