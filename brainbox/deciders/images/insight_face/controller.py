from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel,
    File
)
from .settings import InsightFaceSettings
from pathlib import Path
import os

class InsightFaceController(
    DockerWebServiceController[InsightFaceSettings],
    INotebookableController
):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES.split('\n'),
        )


    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        config = RunConfiguration(
            publish_ports={self.settings.connection.port: 8084},
        )
        return config

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return InsightFaceSettings()

    def create_api(self):
        from .api import InsightFace
        return InsightFace()

    def post_install(self):
        pass


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import InsightFace
        file = File.read(Path(__file__).parent / 'files/image.png')


        result = api.execute(BrainBoxTask.call(InsightFace).analyze(image=file))
        yield TestReport.last_call(api)

        tc.assertEqual(5, len(result))



DOCKERFILE = f'''
FROM python:3.11.11

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

RUN pip freeze

COPY . /home/app/insightface

WORKDIR /home/app/insightface

ENTRYPOINT ["python3","/home/app/insightface/main.py"]
'''

ORIGINAL_DEPENDENCIES = '''
flask
insightface
onnxruntime
opencv-python-headless
numpy
notebook
'''


DEPENDENCIES = '''
albucore==0.0.24
albumentations==2.0.8
annotated-types==0.7.0
anyio==4.10.0
argon2-cffi==25.1.0
argon2-cffi-bindings==25.1.0
arrow==1.3.0
asttokens==3.0.0
async-lru==2.0.5
attrs==25.3.0
babel==2.17.0
beautifulsoup4==4.13.5
bleach==6.2.0
blinker==1.9.0
certifi==2025.8.3
cffi==1.17.1
charset-normalizer==3.4.3
click==8.2.1
coloredlogs==15.0.1
comm==0.2.3
contourpy==1.3.3
cycler==0.12.1
Cython==3.1.3
debugpy==1.8.16
decorator==5.2.1
defusedxml==0.7.1
easydict==1.13
executing==2.2.1
fastjsonschema==2.21.2
Flask==3.1.2
flatbuffers==25.2.10
fonttools==4.59.2
fqdn==1.5.1
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
humanfriendly==10.0
idna==3.10
imageio==2.37.0
insightface==0.7.3
ipykernel==6.30.1
ipython==9.5.0
ipython_pygments_lexers==1.1.1
isoduration==20.11.0
itsdangerous==2.2.0
jedi==0.19.2
Jinja2==3.1.6
joblib==1.5.2
json5==0.12.1
jsonpointer==3.0.0
jsonschema==4.25.1
jsonschema-specifications==2025.4.1
jupyter-events==0.12.0
jupyter-lsp==2.3.0
jupyter_client==8.6.3
jupyter_core==5.8.1
jupyter_server==2.17.0
jupyter_server_terminals==0.5.3
jupyterlab==4.4.6
jupyterlab_pygments==0.3.0
jupyterlab_server==2.27.3
kiwisolver==1.4.9
lark==1.2.2
lazy_loader==0.4
MarkupSafe==3.0.2
matplotlib==3.10.6
matplotlib-inline==0.1.7
mistune==3.1.4
ml_dtypes==0.5.3
mpmath==1.3.0
nbclient==0.10.2
nbconvert==7.16.6
nbformat==5.10.4
nest-asyncio==1.6.0
networkx==3.5
notebook==7.4.5
notebook_shim==0.2.4
numpy==2.2.6
onnx==1.19.0
onnxruntime==1.22.1
opencv-python-headless==4.12.0.88
overrides==7.7.0
packaging==25.0
pandocfilters==1.5.1
parso==0.8.5
pexpect==4.9.0
pillow==11.3.0
platformdirs==4.4.0
prettytable==3.16.0
prometheus_client==0.22.1
prompt_toolkit==3.0.52
protobuf==6.32.0
psutil==7.0.0
ptyprocess==0.7.0
pure_eval==0.2.3
pycparser==2.22
pydantic==2.11.7
pydantic_core==2.33.2
Pygments==2.19.2
pyparsing==3.2.3
python-dateutil==2.9.0.post0
python-json-logger==3.3.0
PyYAML==6.0.2
pyzmq==27.0.2
referencing==0.36.2
requests==2.32.5
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rfc3987-syntax==1.1.0
rpds-py==0.27.1
scikit-image==0.25.2
scikit-learn==1.7.1
scipy==1.16.1
Send2Trash==1.8.3
simsimd==6.5.1
six==1.17.0
sniffio==1.3.1
soupsieve==2.8
stack-data==0.6.3
stringzilla==3.12.6
sympy==1.14.0
terminado==0.18.1
threadpoolctl==3.6.0
tifffile==2025.8.28
tinycss2==1.4.0
tornado==6.5.2
tqdm==4.67.1
traitlets==5.14.3
types-python-dateutil==2.9.0.20250822
typing-inspection==0.4.1
typing_extensions==4.15.0
uri-template==1.3.0
urllib3==2.5.0
wcwidth==0.2.13
webcolors==24.11.1
webencodings==0.5.1
websocket-client==1.8.0
Werkzeug==3.1.3
'''