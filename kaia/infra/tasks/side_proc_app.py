from kaia.infra.tasks import TaskCycle, SubprocessConfig
from kaia.infra.tasks.ctors import Ctor
from kaia.infra.comm import Sql
from ..file_io import FileIO
import sys

if __name__ == '__main__':
    cfg = FileIO.read_jsonpickle(sys.argv[1]) #type: SubprocessConfig
    messenger = Sql.file(cfg.db_path).messenger()
    ctor = Ctor(cfg.task_class_path, cfg.task_args, cfg.task_kwargs)
    task = ctor()
    task_cycle = TaskCycle(task, sleep=cfg.sleep)
    task_cycle.run(messenger)


