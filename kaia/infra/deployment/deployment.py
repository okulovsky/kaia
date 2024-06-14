from dataclasses import dataclass
from .builders import IContainerBuilder
from .pushers import IContainerPusher
from .executors import IExecutor, ExecuteOptions, LocalExecutor
from .docker_run import DockerRun

@dataclass
class Deployment:
    builder: IContainerBuilder
    pusher: IContainerPusher
    docker_run: DockerRun
    remote_executor: IExecutor

    @staticmethod
    def kill_by_ancestor_name(executor, ancestor_name):
        command = ['docker', 'ps', '-q', '--filter', f'ancestor={ancestor_name}']
        reply = executor.execute(command, ExecuteOptions(return_output=True))
        container = reply.decode('utf-8').strip()
        if container != '':
            executor.execute(['docker', 'stop', container])
            try:
                executor.execute(['docker', 'rm', container])
            except:
                pass

    def kill(self):
        Deployment.kill_by_ancestor_name(self.remote_executor, self.pusher.get_ancestor())


    def run(self, dont_pull = False):
        self.kill()
        if not dont_pull:
            self.remote_executor.execute_several(self.pusher.get_pull_command())
        if self.docker_run.mount_folders is not None:
            for key in self.docker_run.mount_folders:
                self.remote_executor.create_empty_folder(key)
        run_command = self.docker_run.get_run_command(self.pusher.get_remote_name())
        self.remote_executor.execute(run_command)

    def build(self):
        self.builder.build_container()

    def push(self):
        local_image = self.builder.get_local_name()
        pusher_executor = LocalExecutor()
        pusher_executor.execute_several(self.pusher.get_push_command(local_image))

    def build_and_push(self):
        self.build()
        self.push()



    def make_all(self):
        self.build_and_push()
        self.run()

