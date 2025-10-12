import subprocess
import toml
import yo_fluq
from brainbox.framework import DockerController, BrainboxImageBuilder
from foundation_kaia.misc import Loc
from yo_fluq import FileIO

def resolve_dependencies(controller: DockerController, python_version: str|None = None):
    builder = controller.get_image_builder()
    if not isinstance(builder, BrainboxImageBuilder):
        raise ValueError("Only works with controllers that build with BrainboxImageBuilder")
    with Loc.create_test_folder() as folder:
        deps = FileIO.read_text(builder.context.requirements_original)

        if builder.source_is_python:
            python_version = builder.source_image
        elif python_version is None:
            raise ValueError("Python version is not specified")

        _create_toml(folder, deps, python_version)



        subprocess.check_output([
            'uv',
            'lock',
        ], cwd = folder)

        result = subprocess.check_output([
            'uv', 'export', '--format', 'requirements-txt', '--no-hashes', '--no-annotate'
        ], cwd = folder, text=True)

        clean = "\n".join(
            line for line in result.splitlines()
            if line.strip() != "-e ."
        )
        yo_fluq.FileIO.write_text(clean, builder.context.requirements_lock)


def _create_toml(folder, dependencies_file_content, python_version):
    deps = [d for d in dependencies_file_content.split('\n')]
    clean = []
    for d in deps:
        if '#' in d:
            d = d[:d.index('#')]
        d = d.strip()
        if d == '':
            continue
        clean.append(d)


    data = {
        "project": {
            "name": "temp-project",
            "version": "0.0.1",
            "description": "Temporary project for dependency locking",
            "dependencies": clean,
            "requires-python": '=='+python_version,
        },
    }


    with open(folder/"pyproject.toml", "w", encoding="utf-8") as f:
        toml.dump(data, f)


