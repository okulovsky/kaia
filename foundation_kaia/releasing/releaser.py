from typing import *
from dataclasses import dataclass
from foundation_kaia.misc import Loc
import shutil
from pathlib import Path
import subprocess
import sys
import os
from yo_fluq import FileIO, Query

@dataclass
class Releaser:
    root_folder: Path
    package_name: str
    package_version: str
    module_name: str
    folders_to_export: tuple[str,...]
    files_to_export: tuple[str,...]
    readme_md_generator: Optional[Callable[[], str]] = None
    tox_python: Optional[str] = None
    tox_versions: Optional[Tuple[str,...]] = None
    inner_dependencies: Tuple[str,...] = ()

    def fix_toml_for_tox(self, path):
        lines = []
        with open(path, 'r') as file:
            for line in file:
                bad_line = False
                for dep in self.inner_dependencies:
                    if line.strip() in {f'"{dep}"', f'"{dep}",'}:
                        bad_line=True
                if not bad_line:
                    lines.append(line)
        return ''.join(lines)

    def run_tox(self):
        if self.tox_versions is None:
            raise ValueError(f"Cannot run tox, `tox_versions` are not set")

        commands_pre = []
        if len(self.inner_dependencies) > 0:
            commands_pre.append('commands_pre =')
            for d in self.inner_dependencies:
                location = Query.folder(Loc.temp_folder/f"pypi/{d}/dist/",'*.whl').single()
                commands_pre.append(f'    pip install {location}')

        tox_file = TOX_FILE.format(directory = self.module_name, commands_pre = '\n'.join(commands_pre), pythons = ', '.join(self.tox_versions))
        folder = Loc.temp_folder / 'tox' / self.module_name
        shutil.rmtree(folder, ignore_errors=True)

        shutil.copytree(self.root_folder/self.module_name, folder / self.module_name)
        FileIO.write_text(self.fix_toml_for_tox(self.root_folder/self.module_name/ 'pyproject.toml'), folder/'pyproject.toml')

        with open(folder / 'tox.ini', 'w') as stream:
            stream.write(tox_file)

        to_execute = sys.executable
        if self.tox_python is not None:
            to_execute = self.tox_python
        result = subprocess.call([to_execute, '-m', 'tox', '-rvv'], cwd=folder, env={**os.environ, "PYTHONPATH": ""})
        if result!=0:
            print(f"TESTS FAILED for {self.package_name}")
            exit(0)

    def fix_toml_for_packaging(self, path):
        lines = []
        with open(path, 'r') as file:
            for line in file:
                if line.startswith('version'):
                    lines.append(f'version = "{self.package_version}"\n')
                else:
                    lines.append(line)
        return ''.join(lines)

    @property
    def release_folder(self):
        return Loc.temp_folder / f'pypi/{self.package_name}'

    def package(self):
        release_folder = self.release_folder
        module_release_folder = release_folder / self.module_name
        src_folder = self.root_folder/self.module_name
        shutil.rmtree(release_folder, ignore_errors=True)
        os.makedirs(module_release_folder)

        for folder in self.folders_to_export:
            shutil.copytree(src_folder / folder, module_release_folder / folder)
        for file in self.files_to_export:
            shutil.copy(src_folder / file, module_release_folder / file)

        if self.readme_md_generator is not None:
            doc = self.readme_md_generator()
            FileIO.write_text(doc, src_folder/'README.md')
            FileIO.write_text(doc, release_folder / 'README.md')
        else:
            shutil.copyfile(src_folder/'README.md', release_folder/'README.md')

        toml = self.fix_toml_for_packaging(src_folder/'pyproject.toml')
        FileIO.write_text(toml, src_folder/'pyproject.toml')
        FileIO.write_text(toml, release_folder / 'pyproject.toml')

        os.chdir(release_folder)
        subprocess.check_call([sys.executable, "-m", "build"])

    def deploy(self):
        os.chdir(self.release_folder)
        subprocess.check_call([sys.executable, "-m", "twine", "upload", "dist/*"])



TOX_FILE = '''
[tox]
envlist = {pythons}
isolated_build = True

[testenv]
changedir = {directory}/tests
{commands_pre}
commands =
    python -m unittest discover -s . -p "test_*.py"
'''
