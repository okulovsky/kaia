import collections.abc
from pathlib import Path
import json



class StreamingFolderStorageReader(collections.abc.Iterable[bytes]):
    def __init__(self, file_path: Path, temp_file_path: Path, timeout: float = 60):
        self.file_path = file_path
        self.temp_file_path = temp_file_path
        self.timeout = timeout

    def __iter__(self):
        import time
        if not self.file_path.is_file():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        if not self.temp_file_path.exists():
            # Already committed - read the file directly
            with open(self.file_path, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    yield chunk
            return

        # Streaming mode: watch temp file for appended events
        with open(self.file_path, 'rb') as data_file:
            try:
                tmp_fd = open(self.temp_file_path, 'r')
            except FileNotFoundError:
                # Race: temp file disappeared between existence check and open
                while True:
                    chunk = data_file.read(65536)
                    if not chunk:
                        break
                    yield chunk
                return

            try:
                last_chunk_time = time.time()
                while True:
                    line = tmp_fd.readline()
                    if line:
                        try:
                            event = json.loads(line.strip())
                            if event.get('event') == 'appended':
                                size = event.get('size', 0)
                                chunk = data_file.read(size)
                                if chunk:
                                    last_chunk_time = time.time()
                                    yield chunk
                        except (json.JSONDecodeError, KeyError):
                            pass
                    else:
                        # At current EOF of temp file
                        if not self.temp_file_path.exists():
                            if not self.file_path.exists():
                                raise IOError(
                                    f"Upstream job aborted: streaming file was deleted mid-stream: {self.file_path}"
                                )
                            # Normal commit - read any remaining bytes
                            remaining = data_file.read()
                            if remaining:
                                yield remaining
                            return
                        # Still writing, wait for more events
                        if time.time() - last_chunk_time > self.timeout:
                            return
                        time.sleep(0.01)
            finally:
                tmp_fd.close()
