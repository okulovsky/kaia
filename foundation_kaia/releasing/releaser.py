from typing import *
from dataclasses import dataclass
from foundation_kaia.misc import Loc
from foundation_kaia.releasing.mddoc import create_documentation
import shutil
import tarfile
import io
from pathlib import Path
import subprocess
import sys
import os


def file_io_write_text(text, file):
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)


@dataclass
class Releaser:
    root_folder: Path
    package_name: str
    package_version: str
    module_name: str
    folders_to_export: tuple[str,...]
    files_to_export: tuple[str,...]
    tox_python: Optional[str] = None
    tox_versions: Optional[Tuple[str,...]] = None
    inner_dependencies: Tuple[str,...] = ()
    compile_documentation: bool = True
    pre_test_file: Optional[str] = None

    def _export_module(self, destination: Path, extra_folders: tuple[str,...] = ()):
        shutil.rmtree(destination, ignore_errors=True)
        os.makedirs(destination)
        archive = subprocess.run(
            ['git', 'archive', 'HEAD', '--', self.module_name + '/'],
            cwd=self.root_folder,
            capture_output=True,
            check=True
        )
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            tar.extractall(destination, filter='data')

        module_dir = destination / self.module_name
        keep_folders = set(self.folders_to_export) | set(extra_folders)
        keep_files = set(self.files_to_export)
        for item in list(module_dir.iterdir()):
            if item.is_dir() and item.name not in keep_folders:
                shutil.rmtree(item)
            elif item.is_file() and item.name not in keep_files:
                item.unlink()

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

    def run_tox(self) -> str|None:
        if self.tox_versions is None:
            raise ValueError(f"Cannot run tox, `tox_versions` are not set")

        folder = Loc.temp_folder / 'tox' / self.module_name

        commands_pre_lines = []
        if len(self.inner_dependencies) > 0:
            for d in self.inner_dependencies:
                location = next(
                    p for p in (Loc.temp_folder / f"pypi/{d}/dist/").glob("*.whl")
                )
                commands_pre_lines.append(f'pip install {location}')
        if self.pre_test_file is not None:
            commands_pre_lines.append(f'python {folder / self.pre_test_file}')
        commands_pre = ('commands_pre =\n' + '\n'.join(f'    {c}' for c in commands_pre_lines)) if commands_pre_lines else ''

        node_env_vars = ''.join(
            f'    {k} = {os.environ[k]}\n'
            for k in ('NODE_JS_PATH', 'NPM_PATH')
            if k in os.environ
        )
        setenv = (f'setenv =\n{node_env_vars}') if node_env_vars else ''
        tox_file = TOX_FILE.format(directory=self.module_name, commands_pre=commands_pre, pythons=', '.join(self.tox_versions), setenv=setenv)
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder)

        self._export_module(folder, extra_folders=('tests', 'doc'))
        file_io_write_text(self.fix_toml_for_tox(self.root_folder / self.module_name / 'pyproject.toml'), folder / 'pyproject.toml')

        with open(folder / 'tox.ini', 'w') as stream:
            stream.write(tox_file)

        to_execute = sys.executable
        if self.tox_python is not None:
            to_execute = self.tox_python
        result = subprocess.call([to_execute, '-m', 'tox', '-rvv'], cwd=folder, env={**os.environ, "PYTHONPATH": ""})
        if result != 0:
            print(f"TESTS FAILED for {self.package_name}")
            return self.package_name
        return None

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

    def compile_doc(self):
        src_folder = self.root_folder / self.module_name
        doc_folder = src_folder / 'doc'
        doc = create_documentation(doc_folder)
        file_io_write_text(doc, src_folder / 'README.md')

    def package(self):
        release_folder = self.release_folder
        src_folder = self.root_folder / self.module_name
        shutil.rmtree(release_folder, ignore_errors=True)
        os.makedirs(release_folder)

        self.compile_doc()

        self._export_module(release_folder)

        if self.compile_documentation:
            shutil.copyfile(src_folder / 'README.md', release_folder / 'README.md')

        toml = self.fix_toml_for_packaging(src_folder / 'pyproject.toml')
        file_io_write_text(toml, src_folder / 'pyproject.toml')
        file_io_write_text(toml, release_folder / 'pyproject.toml')

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
extras = test
changedir = {directory}/tests
{setenv}
{commands_pre}
commands =
    python -m unittest discover -s . -p "test_*.py"
'''
