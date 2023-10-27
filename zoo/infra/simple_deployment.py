import copy
import os

from kaia.infra import Loc, FileIO
import subprocess
import time
from yo_fluq_ds import *

class Deployment:
    def __init__(self,
                 app_folder: str,
                 entry_point_file: str,
                 docker_url: str,
                 docker_username: str,
                 docker_password: str,
                 ssh_url: str,
                 ssh_username: str,
                 ssh_password: str,
                 open_ports=(7860,),
                 mount_remote_data_folder: Optional[str] = None,
                 propagate_env_variables: Iterable[str] = (),
                 custom_env_variables = None
                 ):
        self.app_folder = app_folder
        self.entry_point_file = entry_point_file
        self.open_ports = open_ports
        self.docker_url = docker_url
        self.docker_password = docker_password
        self.docker_username = docker_username
        self.ssh_url = ssh_url
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.mount_remote_data_folder = mount_remote_data_folder
        self.propagate_env_variables = propagate_env_variables
        self.custom_env_variables = {} if custom_env_variables is None else custom_env_variables


    def _make_dockerfile(self):
        libs = ' '.join(FileIO.read_text(Loc.root_folder/'requirements.linux.txt').split('\n'))


        content = DOCKERFILE_TEMPLATE.format(
            python_version = '3.8',
            install_libraries = 'RUN pip install '+libs,
            folder = self.app_folder,
            entry_point = self.entry_point_file
        )
        FileIO.write_text(content, Loc.root_folder/'Dockerfile')

    def _make_dockerignore(self):
        content = DOCKET_IGNORE_TEMPLACE.format(
            folder = self.app_folder
        )
        FileIO.write_text(content, Loc.root_folder/'.dockerignore')

    def _get_login(self):
        return ['docker','login',self.docker_url,'--username',self.docker_username,'--password',self.docker_password]

    def _push(self, version):
        if subprocess.call(['docker','tag',f'kaia:{version}',f'{self.docker_url}/kaia:latest']) != 0:
            raise ValueError()
        if subprocess.call(self._get_login()) != 0:
            raise ValueError()
        if subprocess.call(['docker','push',f'{self.docker_url}/kaia:latest']) != 0:
            raise ValueError()


    def _ssh(self):
        return [
            'sshpass',
            '-p',
            self.ssh_password,
            'ssh',
            f'{self.ssh_username}@{self.ssh_url}'
        ]

    def _remote_pull(self):
        subprocess.call(self._ssh()+self._get_login())
        subprocess.call(self._ssh()+['docker', 'pull', f'{self.docker_url}/kaia:latest'])


    def deploy(self):
        version = str(int(time.time()))
        self._make_dockerignore()
        self._make_dockerfile()
        subprocess.call(['docker','build',Loc.root_folder, '--tag', f'kaia:{version}'])
        return version

    def _get_run_local(self, image):
        ports = Query.en(self.open_ports).select_many(lambda z: ['-p', f'{z}:{z}']).to_list()
        args = ['docker', 'run'] + ports + [image]
        return args

    def run_local(self, version):
        subprocess.call(self._get_run_local(f'kaia:{version}'))

    def kill_remote(self):
        reply = subprocess.check_output(self._ssh()+
                                      ['docker',
                                       'ps',
                                       '-q',
                                       '--filter',
                                       f'ancestor={self.docker_url}/kaia',
                                       ])
        container = reply.decode('utf-8').strip()
        if container!='':
            subprocess.call(self._ssh()+['docker','stop',container])


    def _get_run(self, image):
        ports = Query.en(self.open_ports).select_many(lambda z: ['-p', f'{z}:{z}']).to_list()
        mount = []
        if self.mount_remote_data_folder is not None:
            mount = ['--mount', f'type=bind,source={self.mount_remote_data_folder},target=/data']

        envs = []
        env_dict = copy.deepcopy(self.custom_env_variables)
        for var in self.propagate_env_variables:
            env_dict[var] = os.environ[var]
        for var, value in env_dict.items():
            environment_quotation= '"'
            envs.append('--env')
            envs.append(f'{environment_quotation}{var}={value}{environment_quotation}')
        args = ['docker', 'run'] + ports + mount + envs + [image]
        return args

    def run_remote(self, version):
        self._push(version)
        self.kill_remote()
        self._remote_pull()
        subprocess.call(self._ssh()+self._get_run(f'{self.docker_url}/kaia:latest'))




DOCKERFILE_TEMPLATE = '''FROM python:{python_version}

{install_libraries}

COPY ./kaia /kaia

COPY ./zoo /zoo

COPY ./{folder} /{folder}

COPY setup.py /setup.py

RUN pip install -e .

CMD ["python3","/{folder}/{entry_point}"]
'''

DOCKET_IGNORE_TEMPLACE = '''
# Ignore everything
*

# Allow files and directories
!/kaia
!/zoo
!/{folder}
!/setup.py

# Ignore unnecessary files inside allowed directories
# This should go after the allowed directories
**/*.pyc

'''