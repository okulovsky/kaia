from foundation_kaia.marshalling import Server, ServiceComponent, ThreadTestApi, ApiCall
from brainbox.framework.job_processing.core.command_queue import CommandQueue
from .interface import IJobsService
from .service import JobsService


class JobsApi(IJobsService):
    def __init__(self, base_url: str):
        ApiCall.define_endpoints(self, base_url, IJobsService)

    @staticmethod
    def test(engine, port: int = 18195) -> 'ThreadTestApi[JobsApi]':
        return ThreadTestApi(JobsApi, Server(port, ServiceComponent(JobsService(engine, CommandQueue()))))
