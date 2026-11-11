from chara import Chara

from ..io import read_json, write_json


def call_local(function, *args):
    path = Chara.current.folder / "local_attempts.json"
    history = read_json(path) if path.exists() else []
    index = 0
    attempted = 0
    while True:
        if index == len(history):
            history.append("pending")
            write_json(path, history)
        previous = history[index]
        try:
            return Chara.call(function, f"attempt_{index:04d}")(*args)
        except Exception as error:
            history[index] = "failed"
            write_json(path, history)
            if previous != "failed":
                attempted += 1
                if (
                    isinstance(
                        error, (ValueError, FileNotFoundError, ImportError, MemoryError)
                    )
                    or attempted >= 3
                ):
                    raise
            index += 1
