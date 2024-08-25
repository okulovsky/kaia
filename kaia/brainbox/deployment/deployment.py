from .container_runner import IContainerRunner
from .image_source import IImageSource
from .image_builder import IImageBuilder
from .executor import IExecutor

class Deployment:
    def __init__(self,
                 source: IImageSource,
                 runner: IContainerRunner,
                 executor: IExecutor,
                 builder: None | IImageBuilder = None,
                 build_executor: None|IExecutor = None,
                 ):
        self.builder = builder
        self.source = source
        self.runner = runner
        self.executor = executor
        self.build_executor = build_executor if build_executor is not None else executor


    def build(self) -> 'Deployment':
        name = self.source.get_image_name()
        self.builder.build_image(name, self.build_executor)
        return self

    def push(self) -> 'Deployment':
        self.source.push(self.build_executor)
        return self

    def pull(self) -> 'Deployment':
        self.source.pull(self.executor)
        return self

    def obtain_image(self) -> 'Deployment':
        if self.builder is not None:
            return self.build()
        else:
            return self.pull()


    def stop(self, ignore_errors: bool = True) -> 'Deployment':
        containers = self.source.get_relevant_containers(self.executor)
        containers+=(self.source.get_container_name(),)
        for container in containers:
            try:
                self.executor.execute(['docker','stop',container])
            except:
                if not ignore_errors:
                    raise
        return self

    def remove(self, ignore_errors: bool = True) -> 'Deployment':
        containers = self.source.get_relevant_containers(self.executor)
        containers += (self.source.get_container_name(),)
        for container in containers:
            try:
                self.executor.execute(['docker', 'rm', container])
            except:
                if not ignore_errors:
                    raise
        return self


    def run(self) -> 'Deployment':
        self.runner.run(self.source.get_image_name(), self.source.get_container_name(), self.executor)
        return self



