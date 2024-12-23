from dataclasses import dataclass
from enum import Enum
from .controller_context import MountingPrefix, ControllerContext
from .resource_folder import ResourceFolder
from ...common import Loc
from ...deployment import DockerArgumentsHelper
from copy import deepcopy


@dataclass
class RunConfiguration:
    parameter: str|None
    publish_ports: None | dict[int, int] = None
    mount_resource_folders: None | dict[str, str] = None
    mount_top_resource_folder: bool = True
    propagate_env_variables: None | list[str] = None
    set_env_variables: None | dict[str, str] = None
    command_line_arguments: list[str] | tuple[str, ...] = ()
    custom_flags: tuple[str, ...] | list[str] = ()
    dont_rm: bool = False
    restart_unless_stopped: bool = False
    run_as_root: bool = False
    mount_root_folder: bool = False
    mount_custom_folders: None | dict[str, str] = None

    detach: bool = True
    interactive: bool = True


    def _mounts(self, resource_folder: ResourceFolder, prefix: MountingPrefix):
        if self.mount_resource_folders is not None:
            mount_folders = {
                prefix.remove_from(resource_folder(host_folder)) : container_folder
                for host_folder, container_folder in self.mount_resource_folders.items()
            }
        else:
            mount_folders = {}
        if self.mount_top_resource_folder:
            mount_folders[prefix.remove_from(resource_folder())] = '/resources'
        if self.mount_root_folder:
            mount_folders[prefix.remove_from(Loc.root_folder)] = '/repo'
        if self.mount_custom_folders is not None:
            for key, value in self.mount_custom_folders.items():
                mount_folders[prefix.remove_from(key)] = value
        return mount_folders

    def generate_command(self,
                         container_name: str,
                         image_name: str,
                         context: ControllerContext,
                         ):
        arguments = ['docker', 'run']
        if self.publish_ports is not None:
            arguments += DockerArgumentsHelper.arg_publish_ports(self.publish_ports)
        arguments += DockerArgumentsHelper.arg_mount_folders(self._mounts(context.resource_folder, context.mounting_prefix))
        arguments += DockerArgumentsHelper.arg_propagate_env_variables(self.propagate_env_variables)
        arguments += DockerArgumentsHelper.arg_set_env_variables(self.set_env_variables)
        arguments += ['--gpus', 'all']
        arguments += ['--interactive', '--tty'] if self.interactive else []
        arguments += ['--detach'] if self.detach else []
        arguments += ['--rm'] if not self.dont_rm else []
        arguments += ['--user',f'{context.machine.user_id}:{context.machine.user_id}'] if not self.run_as_root else []
        arguments += ['--restart', 'unless-stopped'] if self.restart_unless_stopped else []
        arguments += list(self.custom_flags)
        arguments += ['--name', container_name]
        arguments += ['--env', f'BRAINBOX_PARAMETER='+('*'+self.parameter if self.parameter is not None else '')]
        arguments += [image_name]
        arguments += list(self.command_line_arguments)
        return arguments

    def as_notebook_service(self):
        configuration = deepcopy(self)
        configuration.command_line_arguments=['--notebook']
        configuration.publish_ports = {8899:8899}
        configuration.mount_data_folder = True
        configuration.mount_custom_folders = {Loc.root_folder: '/repo'}
        configuration.detach = False
        configuration.interactive = False
        return configuration

    def as_service_worker(self, *arguments):
        configuration = deepcopy(self)
        configuration.command_line_arguments = list(arguments)
        configuration.publish_ports = {}
        configuration.mount_top_resource_folder = True
        configuration.detach = False
        configuration.interactive = False
        return configuration
