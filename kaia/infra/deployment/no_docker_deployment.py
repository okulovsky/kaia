import os
from pathlib import Path
from dataclasses import dataclass
from .builders import FullRepoContainerBuilder
from .executors import IExecutor
import shutil


@dataclass
class NoDockerDeployment:
    container_builder: FullRepoContainerBuilder
    executor: IExecutor
    conda_path: str
    remote_path: str
    env_name: str = 'env'


    def get_src_path(self):
        return self.remote_path + '/src'


    def deliver(self):
        path = self.container_builder._make_all_files()
        from yo_fluq_ds import Query
        pyc_files = Query.folder(path,'**/*.pyc').to_list()
        for file in pyc_files:
            os.unlink(file)
        shutil.make_archive(path, 'zip', path)
        zip_path = path.parent / (path.name + '.zip')
        remote_zip = self.remote_path+'/archive.zip'
        self.executor.upload_file(zip_path, remote_zip)
        src = self.get_src_path()
        self.executor.execute(f'rm -rf {src}')
        self.executor.execute(f'mkdir {src}')
        self.executor.execute(f'cd {src}; unzip {remote_zip}')

    def setup_environment(self):
        self.executor.execute(f'{self.conda_path}/bin/conda remove --name {self.env_name} --all -y')
        self.executor.execute(f'{self.conda_path}/bin/conda create --name {self.env_name} python={self.container_builder.python_version} -y')
        self.executor.execute(f'{self.conda_path}/envs/{self.env_name}/bin/python -m pip install '+' '.join(self.container_builder.dependencies))

    def run(self):
        self.executor.execute(f'{self.conda_path}/envs/{self.env_name}/bin/python -m pip install -e {self.get_src_path()}')
        self.executor.execute(f'{self.conda_path}/envs/{self.env_name}/bin/python {self.get_src_path()}/entry.py')




