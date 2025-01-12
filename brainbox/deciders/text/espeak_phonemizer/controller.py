from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel
)
from .settings import EspeakPhonemizerSettings
from pathlib import Path


class EspeakPhonemizerController(
    DockerWebServiceController[EspeakPhonemizerSettings],
    INotebookableController,
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
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return EspeakPhonemizerSettings()

    def create_api(self):
        from .api import EspeakPhonemizer
        return EspeakPhonemizer()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import EspeakPhonemizer

        api.execute(BrainBoxTask.call(EspeakPhonemizer).phonemize("This is some text"))

        yield (
            TestReport
            .last_call(api)
            .href('en-pho')
            .with_comment("Phonemizes one english line")
        )

        api.execute(BrainBoxTask.call(EspeakPhonemizer).phonemize(["This is some text", "This is the second line"]))

        yield (
            TestReport
            .last_call(api)
            .href('en-pho-2')
            .with_comment("Phonemizes several english lines")
        )

        api.execute(BrainBoxTask.call(EspeakPhonemizer).phonemize("Keep the stress marks", stress=True))
        yield (
            TestReport
            .last_call(api)
            .href('stress')
            .with_comment("Phonemizes keeping the stress marks")
        )

        api.execute(BrainBoxTask.call(EspeakPhonemizer).phonemize('Das is ein Satz', language='de'))
        yield (
            TestReport
                .last_call(api)
                .href('de')
                .with_comment("Phonemizes German")
        )





DOCKERFILE = f'''
FROM python:3.8

{SmallImageBuilder.APT_INSTALL('libespeak-ng1')}

{{{SmallImageBuilder.ADD_USER_PLACEHOLDER}}}

{{{SmallImageBuilder.PIP_INSTALL_PLACEHOLDER}}}

RUN pip freeze

COPY . /home/app/

ENTRYPOINT ["python3","/home/app/main.py"]
'''

DEPENDENCIES = '''
anyio==4.5.2
argon2-cffi==23.1.0
argon2-cffi-bindings==21.2.0
arrow==1.3.0
asttokens==3.0.0
async-lru==2.0.4
attrs==24.3.0
babel==2.16.0
backcall==0.2.0
beautifulsoup4==4.12.3
bleach==6.1.0
blinker==1.8.2
certifi==2024.12.14
cffi==1.17.1
charset-normalizer==3.4.1
click==8.1.8
comm==0.2.2
debugpy==1.8.11
decorator==5.1.1
defusedxml==0.7.1
espeak-phonemizer==1.3.1
exceptiongroup==1.2.2
executing==2.1.0
fastjsonschema==2.21.1
Flask==3.0.3
fqdn==1.5.1
h11==0.14.0
httpcore==1.0.7
httpx==0.28.1
idna==3.10
importlib_metadata==8.5.0
importlib_resources==6.4.5
ipykernel==6.29.5
ipython==8.12.3
isoduration==20.11.0
itsdangerous==2.2.0
jedi==0.19.2
Jinja2==3.1.5
json5==0.10.0
jsonpointer==3.0.0
jsonschema==4.23.0
jsonschema-specifications==2023.12.1
jupyter-events==0.10.0
jupyter-lsp==2.2.5
jupyter_client==8.6.3
jupyter_core==5.7.2
jupyter_server==2.14.2
jupyter_server_terminals==0.5.3
jupyterlab==4.3.4
jupyterlab_pygments==0.3.0
jupyterlab_server==2.27.3
MarkupSafe==2.1.5
matplotlib-inline==0.1.7
mistune==3.1.0
nbclient==0.10.1
nbconvert==7.16.5
nbformat==5.10.4
nest-asyncio==1.6.0
notebook==7.3.2
notebook_shim==0.2.4
overrides==7.7.0
packaging==24.2
pandocfilters==1.5.1
parso==0.8.4
pexpect==4.9.0
pickleshare==0.7.5
pkgutil_resolve_name==1.3.10
platformdirs==4.3.6
prometheus_client==0.21.1
prompt_toolkit==3.0.48
psutil==6.1.1
ptyprocess==0.7.0
pure_eval==0.2.3
pycparser==2.22
Pygments==2.19.1
python-dateutil==2.9.0.post0
python-json-logger==3.2.1
pytz==2024.2
PyYAML==6.0.2
pyzmq==26.2.0
referencing==0.35.1
requests==2.32.3
rfc3339-validator==0.1.4
rfc3986-validator==0.1.1
rpds-py==0.20.1
Send2Trash==1.8.3
six==1.17.0
sniffio==1.3.1
soupsieve==2.6
stack-data==0.6.3
terminado==0.18.1
tinycss2==1.2.1
tomli==2.2.1
tornado==6.4.2
traitlets==5.14.3
types-python-dateutil==2.9.0.20241206
typing_extensions==4.12.2
uri-template==1.3.0
urllib3==2.2.3
wcwidth==0.2.13
webcolors==24.8.0
webencodings==0.5.1
websocket-client==1.8.0
Werkzeug==3.0.6
zipp==3.20.2
'''

