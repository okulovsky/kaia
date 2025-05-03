import os
import shutil
import subprocess
import sys
from brainbox.framework import Loc
from pathlib import Path
from brainbox.release.documentation_handler import create_documentation
from yo_fluq import FileIO

def package_and_deploy(folder_path):
    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        sys.exit(1)

    # Change to the project directory
    os.chdir(folder_path)

    # Clean previous builds if any
    dist_dir = os.path.join(folder_path, "dist")
    if os.path.exists(dist_dir):
        print("Cleaning previous builds...")
        for file in os.listdir(dist_dir):
            os.remove(os.path.join(dist_dir, file))

    # Build the package using pyproject.toml
    print("Building the package...")
    subprocess.check_call([sys.executable, "-m", "build"])

    # Upload to PyPI
    print("Uploading the package to PyPI...")
    subprocess.check_call([sys.executable, "-m", "twine", "upload", "dist/*"])

def make_all():
    release_folder = Loc.temp_folder/'brain_box_pypi'
    bb_release_folder = release_folder/'brainbox'
    src_folder = Path(__file__).parent.parent
    shutil.rmtree(release_folder, ignore_errors=True)
    os.makedirs(bb_release_folder)

    for folder in ['framework', 'deciders', 'doc', 'flow']:
        shutil.copytree(src_folder/folder, bb_release_folder/folder)
    for file in ['run.py', 'run_test.py','__init__.py']:
        shutil.copy(src_folder/file, bb_release_folder/file)


    FileIO.write_text(create_documentation(), release_folder/'README.md')
    shutil.copy(Path(__file__).parent/'pyproject.toml', release_folder)
    package_and_deploy(release_folder)


if __name__ == '__main__':
    make_all()


