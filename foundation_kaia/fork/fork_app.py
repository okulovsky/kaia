from typing import *
from dataclasses import dataclass
from .fork import Fork

@dataclass
class ForkApp:
    main: Optional[Callable] = None
    supporting: Tuple[Callable,...] = ()
    _forks = []

    def run(self):
        for service in self.supporting:
            self._forks.append(Fork(service).start())
        if self.main is not None:
            self.main()

    def terminate(self):
        for fork in reversed(self._forks):
            fork.terminate()

    def __enter__(self):
        if self.main is not None:
            raise ValueError("Can only enter/exit in the app without main routine")
        self.run()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()



