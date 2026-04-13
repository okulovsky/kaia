from foundation_kaia.marshalling import Server, ServiceComponent, ThreadTestApi, ApiCall
from brainbox.framework.job_processing.core.command_queue import CommandQueue
from .interface import ITasksService
from .service import TasksService


class TasksApi(ITasksService):
    def __init__(self, base_url: str):
        ApiCall.define_endpoints(self, base_url, ITasksService)

    @staticmethod
    def test(engine, port: int = 18195) -> 'ThreadTestApi[TasksApi]':
        return ThreadTestApi(TasksApi, Server(port, ServiceComponent(TasksService(engine, CommandQueue()))))
