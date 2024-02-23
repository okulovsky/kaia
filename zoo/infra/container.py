import os
import pickle
from typing import *
from dataclasses import dataclass
from pathlib import Path
import shutil
from yo_fluq_ds import FileIO
from kaia.infra import Loc
import datetime
import subprocess
from .container_pusher import ContainerPusher


@dataclass
class Container:
    name: str
    tag: str
    entry_point: Any
    dependencies: List[str]
    deployed_folders: Iterable[str]
    pusher: Optional[ContainerPusher]
    python_version: str = '3.8'
    root_path: Optional[Path] = None
    additional_dependencies: Optional[Iterable[Iterable[str]]] = None
    custom_dockerfile_template: str = None
    custom_entryfile_template: str = None
    custom_setup_py_template: str = None
    custom_dockerignore_template: str = None


    def _make_pip_install(self, deps: Iterable[str]):
        deps = list(deps)
        if len(deps) == 0:
            return ''
        libs = ' '.join(deps)
        return 'RUN pip install ' + libs

    def _make_dockerfile(self):
        dockerfile_template = DOCKERFILE_TEMPLATE
        if self.custom_dockerfile_template is not None:
            dockerfile_template = self.custom_dockerfile_template

        folders = list(self.deployed_folders)

        install_libraries = self._make_pip_install(self.dependencies)
        if self.additional_dependencies is not None:
            for dep_list in self.additional_dependencies:
                install_libraries+='\n\n'+self._make_pip_install(dep_list)

        content = dockerfile_template.format(
            python_version=self.python_version,
            install_libraries=install_libraries,
        )
        return content

    def _make_entryfile(self):
        entryfile_template = ENTRYFILE_TEMPLATE
        if self.custom_entryfile_template is not None:
            entryfile_template = self.custom_entryfile_template

        return entryfile_template.format(name=self.name, version=self.tag)

    def _make_setup_py(self):
        template = SETUP_PY_TEMPLATE
        if self.custom_setup_py_template is not None:
            template = self.custom_setup_py_template
        return template.format(name=self.name, version = self.tag)


    def _make_dockerignore(self):
        template = DOCKER_IGNORE_TEMPLATE
        if self.custom_dockerignore_template is not None:
            template = self.custom_dockerignore_template
        return template


    def _make_deploy_folder(self, root_path: Path, docker_path: Path):
        shutil.rmtree(docker_path, ignore_errors=True)
        os.makedirs(docker_path)
        FileIO.write_text(self._make_dockerfile(), docker_path/'Dockerfile')
        FileIO.write_text(self._make_setup_py(), docker_path/'setup.py')
        FileIO.write_text(self._make_dockerignore(), docker_path/'.dockerignore')
        FileIO.write_text(self._make_entryfile(), docker_path/'entry.py')
        for folder in self.deployed_folders:
            shutil.copytree(root_path/folder, docker_path/folder)


    def build(self):
        root_path = self.root_path
        if root_path is None:
            root_path = Loc.root_path
        docker_path = Loc.temp_folder/'deployments'/str(datetime.datetime.now().timestamp())
        self._make_deploy_folder(root_path, docker_path)
        with open(docker_path / 'entry.pkl', 'wb') as file:
            pickle.dump(self.entry_point, file)
        arguments = ['docker', 'build', str(docker_path), '--tag', f'{self._docker_conform_name(self.name)}:{self.tag}']
        if subprocess.call(arguments) != 0:
            raise ValueError(f'Docker call caused an error. Arguments\n{" ".join(arguments)}')
        shutil.rmtree(docker_path)

    def _docker_conform_name(self, name: str):
        return name.lower()

    def push(self):
        if self.pusher is None:
            raise ValueError('Push is requested, but no pusher is set')
        self.pusher.push(self._docker_conform_name(self.name), self.tag)

    def get_remote_name(self):
        if self.pusher is None:
            raise ValueError('get_remote_name is requested, but no pusher is set')
        return self.pusher.get_remote_name(self._docker_conform_name(self.name), self.tag)








ENTRYFILE_TEMPLATE = '''
from pathlib import Path
import pickle

with open(Path(__file__).parent/"entry.pkl",'rb') as file:
    entry_point = pickle.load(file)
    
entry_point()

'''


DOCKERFILE_TEMPLATE = '''FROM python:{python_version}

{install_libraries}

COPY . /

RUN pip install -e .

CMD ["python3","/entry.py"]
'''

DOCKER_IGNORE_TEMPLATE = '''
**/*.pyc
'''

SETUP_PY_TEMPLATE = '''
from setuptools import setup, find_packages

setup(name='{name}',
      version='{version}',
      packages=find_packages(),
      install_requires=[
      ],
      include_package_data = True,
      zip_safe=False)
'''
