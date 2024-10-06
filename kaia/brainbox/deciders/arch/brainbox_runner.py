from kaia.brainbox.deployment import IContainerRunner, Command, IExecutor
from dataclasses import dataclass
from pathlib import Path
from .docker_installer import DockerInstaller
from enum import Enum

@dataclass
class BrainBoxServiceRunner(IContainerRunner):
    class GpuRequirement(Enum):
        No = 0
        Preffered = 1
        Mandatory = 2




    publish_ports: None|dict[int,int] = None
    mount_resource_folders: None|dict[str, str] = None
    propagate_env_variables: None|list[str] = None
    set_env_variables: None|dict[str,str] = None
    gpu_required: 'BrainBoxServiceRunner.GpuRequirement' = GpuRequirement.No
    vram_in_gb_required: None|int = None
    command_line_arguments: list[str]|tuple[str,...] = ()
    custom_flags: tuple[str,...]|list[str] = ()
    mount_data_folder: bool = True
    dont_rm_debug_only: bool = False
    restart_unless_stopped: bool = False
    run_as_root: bool = False

    _installer: None | DockerInstaller = None
    _mount_folders: None|dict[str,str] = None
    _detach: bool = True
    _interactive: bool = True


    def _gpus(self, executor: IExecutor) -> list[str]:
        gpu = ['--gpus', 'all']
        available_vram = executor.get_machine().vram_in_gb
        if self.gpu_required == BrainBoxServiceRunner.GpuRequirement.No:
            return []
        elif self.gpu_required == BrainBoxServiceRunner.GpuRequirement.Preffered:
            if available_vram is None:
                return []
            elif self.vram_in_gb_required is None:
                return gpu
            elif self.vram_in_gb_required > available_vram:
                return []
            else:
                return gpu
        else:
            if available_vram is None:
                raise ValueError("GPU is required, but non is available")
            elif self.vram_in_gb_required is None:
                return gpu
            elif self.vram_in_gb_required > available_vram:
                raise ValueError(f"Machine has {available_vram}, but {self.vram_in_gb_required} is available")
            else:
                return gpu


    def run(self, image_name: str, container_name: str, executor: IExecutor):
        if self._installer is None:
            raise ValueError("installer was not set!")


        if self.mount_resource_folders is not None:
            mount_folders = {
                self._installer.resource_folder(host_folder) : container_folder
                for host_folder, container_folder in self.mount_resource_folders.items()
            }
        else:
            mount_folders = {}
        if self.mount_data_folder:
            mount_folders[self._installer.resource_folder()] = '/data'

        arguments = (
            ['docker','run']
            + (self.arg_publish_ports(self.publish_ports) if self.publish_ports is not None else [])
            + self.arg_mount_folders(mount_folders)
            + self.arg_mount_folders(self._mount_folders)
            + self.arg_propagate_env_variables(self.propagate_env_variables)
            + self.arg_set_env_variables(self.set_env_variables)
            + self._gpus(executor)
            + ( ['--interactive', '--tty'] if self._interactive else [])
            + ['--name', container_name]
            + ( ['--detach'] if self._detach else [])
            + ( ['--rm'] if not self.dont_rm_debug_only else [] )
            + (['--user', f'{executor.get_machine().user_id}:{executor.get_machine().user_id}'] if not self.run_as_root else [])
            + ( ['--restart', 'unless-stopped'] if self.restart_unless_stopped else [])
            + list(self.custom_flags)
            + [image_name]
            + list(self.command_line_arguments)
        )
        executor.execute(arguments)



