import subprocess
from typing import Iterable, List, Union


class SubprocessError(RuntimeError):
    """Raised when subprocess exits with non-zero code."""

    def __init__(self, returncode: int, cmd: List[str]):
        super().__init__(f"Command {cmd!r} exited with code {returncode}")
        self.returncode = returncode
        self.cmd = cmd


def subprocess_streaming_call(
    cmd: Union[str, List[str]],
    *,
    shell: bool = False,
    cwd: str | None = None,
    env: dict | None = None,
) -> Iterable[str]:
    """
    Run command and yield its output line by line.

    Raises SubprocessError if process exits with non-zero code.
    """
    proc = subprocess.Popen(
        cmd,
        shell=shell,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # line buffered
    )

    assert proc.stdout is not None  # for typing

    try:
        for line in proc.stdout:
            print(line)
            yield line.rstrip("\n")
    finally:
        proc.stdout.close()

    returncode = proc.wait()
    if returncode != 0:
        raise SubprocessError(returncode, cmd if isinstance(cmd, list) else [cmd])
