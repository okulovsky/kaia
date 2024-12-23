import os

from brainbox.controllers.deployment import SmallImageBuilder, LocalExecutor, IImageBuilder, IExecutor
from pathlib import Path
import shutil
import toml
from brainbox.framework.common import Loc


class BrainboxImageBuilder(IImageBuilder):
    def build_image(self, image_name: str, exec: IExecutor) -> None:
        TARGET_FOLDER = Loc.temp_folder/'brainbox_deployment'
        shutil.rmtree(TARGET_FOLDER, ignore_errors=True)
        CODE_FOLDER = Path(__file__).parent.parent
        shutil.copytree(Path(__file__).parent/'deployment_folder', TARGET_FOLDER)
        shutil.copytree(CODE_FOLDER, TARGET_FOLDER/'brainbox')


        with open(TARGET_FOLDER/'pyproject.toml','r') as file:
            project = toml.load(file)
        dependencies = project['project']['dependencies']
        SmallImageBuilder(
            TARGET_FOLDER,
            TEMPLATE,
            dependencies,
        ).build_image(image_name, exec)




TEMPLATE = f'''
FROM python:3.11

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY . /home/app/

RUN pip install -e /home/app

ENTRYPOINT ["python", "/home/app/brainbox/tools/run_brainbox_controllers.py"]

'''




if __name__ == '__main__':
    pass