from dataclasses import dataclass, field
from foundation_kaia.marshalling_2 import JSON
from typing import Dict, Union, List, Iterable
from .job_request import JobRequest, JobDescription, IJobRequestFactory
from uuid import uuid4

@dataclass
class BrainBoxTaskOptionals:
    id: str|None
    parameter: str|None
    batch: str|None
    info: JSON


class JobRequestCollector:
    def __init__(self,):
        self.id_map: dict[int, str] = {}
        self.ordered: list[BrainBoxTask] = []

    def collect(self, task: 'BrainBoxTask'):
        if id(task) in self.id_map:
            return

        self.id_map[id(task)] = task.optionals.id if task.optionals.id is not None else str(uuid4())
        self.ordered.append(task)

        for dep in task.dependencies.values():
            if isinstance(dep, BrainBoxTask):
                self.collect(dep)
        for dep in task.fake_dependencies:
            if isinstance(dep, BrainBoxTask):
                self.collect(dep)

    def to_job_descriptions(self) -> tuple[JobDescription,...]:
        result = []
        for t in self.ordered:
            resolved_deps = {
                name: self.id_map[id(dep)] if isinstance(dep, BrainBoxTask) else dep
                for name, dep in t.dependencies.items()
            }
            for i, dep in enumerate(t.fake_dependencies):
                resolved_deps['*fake_dependency_' + str(i)] = (
                    self.id_map[id(dep)] if isinstance(dep, BrainBoxTask) else dep
                )

            result.append(JobDescription(
                id=self.id_map[id(t)],
                decider=t.decider,
                parameter=t.optionals.parameter,
                method=t.method,
                arguments=t.arguments,
                info=t.optionals.info,
                batch=t.optionals.batch,
                ordering_token=t.ordering_token,
                dependencies=resolved_deps,
            ))
        return tuple(result)


@dataclass
class BrainBoxTask(IJobRequestFactory):
    decider: str
    method: str
    arguments: dict[str, JSON]
    dependencies: Dict[str, Union[str,'BrainBoxTask']] = field(default_factory=dict)
    fake_dependencies: List[Union[str,'BrainBoxTask']] = field(default_factory=list)
    ordering_token: str = ''
    optionals: BrainBoxTaskOptionals = field(default_factory=BrainBoxTaskOptionals)

    def to_job_request(self) -> JobRequest:
        collector = JobRequestCollector()
        collector.collect(self)
        return JobRequest(collector.to_job_descriptions())

    @staticmethod
    def several_to_job_descriptions(tasks: Iterable['BrainBoxTask']) -> tuple[JobDescription,...]:
        collector = JobRequestCollector()
        for task in tasks:
            collector.collect(task)
        return collector.to_job_descriptions()






