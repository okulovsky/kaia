import os
from pathlib import Path
from kaia.infra import Loc, deployment
from .settings import SnipsNLUSettings
from ..docker_based import DockerBasedInstaller, DockerBasedInstallerEndpoint
from kaia.brainbox.deciders.api.snips_nlu import SnipsNLUApi
from unittest import TestCase
import yaml


class SnipsNLUInstaller(DockerBasedInstaller):
    def __init__(self, settings: SnipsNLUSettings):
        self.settings = settings
        builder = deployment.SmallContainerBuilder(
            self.settings.image_name,
            Path(__file__).parent/'container',
            DOCKERFILE,
            DEPENDENCIES
            )

        notebook_config = deployment.DockerRun(
            open_ports=[8899],
            mount_folders={Loc.root_folder:'/repo'},
            additional_arguments=[ '--rm'],
            command_line_arguments=['notebook']
        )

        self.notebook_endpoint = DockerBasedInstallerEndpoint(self, notebook_config)

        service_config = deployment.DockerRun(
            mapped_ports={8084:self.settings.port},
            additional_arguments=['--rm','-d','-it'],
            mount_folders={self.settings.data_folder:'/data'}
        )

        self.service_endpoint = DockerBasedInstallerEndpoint(self, service_config, 5, self.settings.port)

        super().__init__(builder)





    def get_service_endpoint(self) -> DockerBasedInstallerEndpoint:
        return self.service_endpoint


    def install(self):
        self.get_service_endpoint().kill()
        os.makedirs(self.settings.data_folder,exist_ok=True)
        self.build()


    def create_api(self):
        return SnipsNLUApi(f'{self.settings.address}:{self.settings.port}')


    def self_test(self, tc: TestCase):
        self.service_endpoint.run()
        with open(Path(__file__).parent/'dataset.yaml', 'r') as file:
            data = list(yaml.load_all(file,yaml.FullLoader))
        self.create_api().train('test',data)
        result = self.create_api().parse('test', "Hey, lights on in the lounge !")
        tc.assertEqual('turnLightOn', result['intent']['intentName'])
        tc.assertEqual('living room', result['slots'][0]['value']['value'])

        result = self.create_api().parse('test', "I'm eating sandwich")
        tc.assertIsNone(result['intent']['intentName'])
        self.service_endpoint.kill()





DOCKERFILE = '''
FROM python:3.8

RUN apt update

RUN apt install rustc -y

RUN pip install setuptools_rust==1.9.0

RUN pip install {dependencies}

RUN pip freeze

RUN python3 -m snips_nlu download en

COPY . /kaia

ENTRYPOINT ["python3","/kaia/main.py"]
'''

DEPENDENCIES_NOTEBOOK = '''
asttokens==2.0.3
attrs==19.3.0
backcall==0.1.0
beautifulsoup4==4.8.2
bleach==3.1.0
decorator==4.4.1
defusedxml==0.6.0
executing==0.4.1
fastjsonschema==2.14.2
importlib_metadata==1.4.0
importlib_resources==1.0.2
ipykernel==5.1.3
ipython==7.11.1
ipython-genutils==0.2.0
jedi==0.15.2
Jinja2==2.10.3
jsonschema==3.2.0
jupyter_client==5.3.4
jupyter_core==4.6.1
jupyterlab_pygments==0.1.0
MarkupSafe==1.1.1
mistune==0.8.4
nbconvert==5.6.1
nbformat==5.0.3
nest-asyncio==1.2.2
notebook==6.0.2
pandocfilters==1.4.2
parso==0.5.2
pexpect==4.7.0
pickleshare==0.7.5
prometheus_client==0.7.1
prompt_toolkit==3.0.2
psutil==5.6.7
ptyprocess==0.6.0
pure-eval==0.0.3
Pygments==2.5.2
python-dateutil==2.8.1
pyzmq==18.1.0
Send2Trash==1.5.0
soupsieve==1.9.5
stack-data==0.0.6
terminado==0.8.3
tinycss2==1.0.2
tornado==6.0.3
traitlets==4.3.3
typing_extensions==3.7.4.1
webencodings==0.5.1
zipp==1.0.0
'''


DEPENDENCIES_SNIPS = '''
cached-property==1.5.2
certifi==2019.11.28
chardet==3.0.4
charset_normalizer==1.3.4
deprecation==2.0.7
docopt==0.6.2
dragonmapper==0.2.7
future==0.17.1
hanzidentifier==1.2.0
idna==2.8
joblib==0.14.1
loguru==0.7.2
num2words==0.5.10
numpy==1.18.1
packaging==20.0
prettytable==3.10.0
pyaml==19.12.0
pyparsing==3.1.2
python-crfsuite==0.9.6
PyYAML==5.3
requests==2.22.0
scikit-learn==0.22.1
scipy==1.4.1
semantic-version==2.8.4
setuptools-rust==0.10.6
six==1.14.0
sklearn-crfsuite==0.3.6
snips-nlu==0.20.2
snips-nlu-parsers==0.4.2
snips-nlu-utils==0.9.1
tabulate==0.8.6
toml==0.10.2
tomli==2.0.1
tqdm==4.41.1
urllib3==1.25.7
wcwidth==0.2.13
zhon==2.0.2
'''

DEPENDENCIES_FLASK = '''
click==7.0
Flask==1.1.1
itsdangerous==1.1.0
Werkzeug==0.16.0
'''

DEPENDENCIES = DEPENDENCIES_FLASK  + DEPENDENCIES_SNIPS + DEPENDENCIES_NOTEBOOK
