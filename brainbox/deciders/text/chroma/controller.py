from typing import Iterable
from unittest import TestCase

from brainbox import BrainBoxTask
from .settings import ChromaSettings
from brainbox.framework import (
    DockerWebServiceController, IImageBuilder, SmallImageBuilder, RunConfiguration,
    INotebookableController, BrainBoxApi, TestReport)
from pathlib import Path

from brainbox.framework.controllers.controller.controller import TSettings


class ChromaController(
    DockerWebServiceController[ChromaSettings],
    INotebookableController
):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent / "container",
            DOCKERFILE,
            DEPENDENCIES.split("\n")
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:5252},
        )

    def create_api(self):
        from .api import Chroma
        return Chroma()

    def get_default_settings(self) -> TSettings:
        return ChromaSettings()

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()


    # В качестве тестового текста взята 1-ая глава из книги "Гарри Поттер и филосовский камень"
    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Chroma

        query = "What happened to Harry Potter?"

        api.execute(
            BrainBoxTask.call(Chroma)
            .get_relevant_context(query=query)
        )

        yield (
            TestReport
            .last_call(api)
            .href('get_relevant_context')
        )


DOCKERFILE = f'''
FROM python:3.11

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

WORKDIR /home/app

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

COPY . .

ENTRYPOINT ["python3","/home/app/main.py"]
'''

DEPENDENCIES = '''
aiohappyeyeballs==2.6.1
aiohttp==3.11.14
aiosignal==1.3.2
annotated-types==0.7.0
anyio==4.9.0
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
arrow==1.3.0
asgiref==3.8.1
asttokens==3.0.0
async-lru==2.0.5
async-timeout==4.0.3
attrs==25.3.0
babel==2.17.0
backoff==1.11.1
bcrypt==4.3.0
beautifulsoup4==4.13.3
blinker==1.9.0
cached-property==1.5.2
cached_property==1.5.2
cachetools==5.5.2
certifi==2025.1.31
cffi==1.17.1
charset-normalizer==3.4.1
chroma-hnswlib==0.7.6
chromadb==0.6.3
click==8.1.8
colorama==0.4.6
coloredlogs==15.0.1
comm==0.2.2
contourpy==1.3.1
cryptography==44.0.2
cycler==0.12.1
datasets==2.14.4
debugpy==1.8.13
decorator==5.2.1
defusedxml==0.7.1
deprecated==1.2.18
dill==0.3.7
dnspython==2.7.0
durationpy==0.9
email-validator==2.2.0
email_validator==2.2.0
et_xmlfile==2.0.0
exceptiongroup==1.2.2
executing==2.1.0
fastapi==0.115.12
fastapi-cli==0.0.7
filelock==3.18.0
fonttools==4.56.0
fqdn==1.5.1
frozenlist==1.5.0
fsspec==2025.3.0
google-auth==2.38.0
googleapis-common-protos==1.69.2
greenlet==3.1.1
grpcio==1.62.2
h11==0.14.0
h2==4.2.0
hpack==4.1.0
httpcore==1.0.7
httptools==0.6.4
httpx==0.28.1
huggingface_hub==0.29.3
humanfriendly==10.0
hyperframe==6.1.0
idna==3.10
importlib-metadata==8.6.1
importlib-resources==6.5.2
importlib_resources==6.5.2
intel-openmp==2024.2.1
ipykernel==6.29.5
ipython==9.0.2
ipython_pygments_lexers==1.1.1
ipywidgets==8.1.5
isoduration==20.11.0
jedi==0.19.2
jinja2==3.1.6
joblib==1.4.2
json5==0.12.0
jsonpatch==1.33
jsonpointer==3.0.0
jsonschema==4.23.0
jsonschema-specifications==2024.10.1
jupyter-lsp==2.2.5
jupyter_client==8.6.3
jupyter_core==5.7.2
jupyter_events==0.12.0
jupyter_server==2.15.0
jupyter_server_terminals==0.5.3
jupyterlab==4.3.6
jupyterlab_pygments==0.3.0
jupyterlab_server==2.27.3
jupyterlab_widgets==3.0.13
langchain==0.3.21
langchain-chroma==0.2.2
langchain-core==0.3.48
langchain-huggingface==0.1.2
langchain-text-splitters==0.3.7
langsmith==0.2.11
markdown-it-py==3.0.0
nbclient==0.10.2
nest-asyncio==1.6.0
networkx==3.4.2
notebook==7.3.3
notebook-shim==0.2.4
numpy==1.26.4
oauthlib==3.2.2
opentelemetry-api==1.31.1
opentelemetry-exporter-otlp-proto-grpc==1.15.0
opentelemetry-instrumentation==0.52b1
opentelemetry-instrumentation-asgi==0.52b1
opentelemetry-instrumentation-fastapi==0.52b1
opentelemetry-proto==1.15.0
opentelemetry-sdk==1.31.1
opentelemetry-semantic-conventions==0.52b1
opentelemetry-util-http==0.52b1
pandas==2.2.3
pandocfilters==1.5.0
parso==0.8.4
patsy==1.0.1
pickleshare==0.7.5
pillow==11.1.0
pip==25.0.1
pkgutil-resolve-name==1.3.10
platformdirs==4.3.7
posthog==3.6.5
prometheus_client==0.21.1
prompt-toolkit==3.0.50
propcache==0.2.1
protobuf==4.25.3
psutil==7.0.0
pulsar-client==3.5.0
pure_eval==0.2.3
pyarrow==17.0.0
pydantic==2.10.6
pydantic-core==2.27.2
pygments==2.19.1
pyjwt==2.10.1
pyopenssl==25.0.0
pyparsing==3.2.3
pypika==0.48.9
pyproject_hooks==1.2.0
pyreadline3==3.5.4
pysocks==1.7.1
python-multipart==0.0.20
pytz==2024.1
pyu2f==0.1.5
pyyaml==6.0.2
pyzmq==26.3.0
referencing==0.36.2
regex==2024.11.6
requests==2.32.3
requests-oauthlib==2.0.0
requests-toolbelt==1.0.0
safetensors==0.5.3
scikit-learn==1.6.1
scipy==1.15.2
seaborn==0.13.2
send2trash==1.8.3
sentence-transformers==4.0.1
setuptools==75.8.2
shellingham==1.5.4
six==1.17.0
sqlalchemy==2.0.39
stack_data==0.6.3
starlette==0.46.1
statsmodels==0.14.4
sympy==1.13.1
tbb==2021.13.0
tenacity==9.0.0
terminado==0.18.1
threadpoolctl==3.6.0
tinycss2==1.4.0
tokenizers==0.21.1
torch==2.6.0
tornado==6.4.2
tqdm==4.67.1
traitlets==5.14.3
transformers==4.50.0
typer==0.15.2
typer-slim==0.15.2
typing-extensions==4.12.2
typing_utils==0.1.0
unicodedata2==16.0.0
uri-template==1.3.0
urllib3==2.3.0
uvicorn==0.34.0
watchfiles==1.0.4
wcwidth==0.2.13
webcolors==24.11.1
webencodings==0.5.1
websocket-client==1.8.0
websockets==15.0.1
wheel==0.45.1
widgetsnbextension==4.0.13
win_inet_pton==1.1.0
'''