from dataclasses import fields as get_dataclass_fields, Field
import inspect
from pathlib import Path
from kaia.infra import FileIO
from ..api import IWorkflow
from ...arch.utils import FileLike
from ....core import BrainBoxTask


class TemplateWorkflow(IWorkflow):
    @staticmethod
    def meta(
            field_name: str|None = None,
            node_title: str|None = None,
            maps_to_job_id: bool = False,
            is_input_file: bool = False,
            is_model_with_priority: None|int = None,
    ):
        return dict(
            field_name=field_name,
            node_title=node_title,
            maps_to_job_id = maps_to_job_id,
            is_input_file = is_input_file,
            is_model_with_priority = is_model_with_priority,
        )

    def find_id_by_title(self, js: dict, title: str) -> list[str]:
        results = []
        for key, value in js.items():
            if value['_meta']['title'] == title:
                results.append(key)
        return results

    def find_single_node_by_title(self, js: dict, title: str) -> dict:
        keys = self.find_id_by_title(js, title)
        if len(keys) == 0:
            raise ValueError(f"Can't find the node with title {title}")
        if len(keys) > 1:
            raise ValueError(f"Too many nodes with title {title}")
        node = js[keys[0]]
        return node

    def find_ids_with_field(self, js: dict, field) -> list[str]:
        results = []
        for key, value in js.items():
            if field in value['inputs']:
                results.append(key)
        return results

    def make_substitution(self, js: dict, field: Field, value: object):
        field_name = field.metadata.get('field_name', None)
        if field_name is None:
            field_name = field.name
        node_title = field.metadata.get('node_title', None)

        if node_title is not None:
            node = self.find_single_node_by_title(js, node_title)
            if field_name not in node['inputs']:
                raise ValueError(f'Field {field_name} not found in the node with title {node_title}')
        else:
            keys = self.find_ids_with_field(js, field_name)
            if len(keys) == 0:
                raise ValueError(f"Can't find the node with field {field_name}")
            if len(keys) > 1:
                raise ValueError(f"Too many nodes with field {field_name}. Specify the title.")
            node = js[keys[0]]

        node['inputs'][field_name] = value

    def read_json(self):
        file = inspect.getfile(self.__class__)
        json_file = Path(file.replace('.py','.json'))
        if not json_file.is_file():
            raise ValueError(f"Cannot find workflow {json_file}."
                f"Workflow must be in the same folder as .py file defining {self.__class__.__name__} and have the same name")
        try:
            js = FileIO.read_json(json_file)
        except:
            raise ValueError(f"Cannot read json file {json_file}")
        return js

    def after_substitution(self, js):
        pass

    def preprocess_value(self, field_name, value):
        return value

    def create_workflow_json(self, job_id: str, decider_parameters: str|None):
        js = self.read_json()

        for field in get_dataclass_fields(type(self)):
            value = getattr(self, field.name)
            if field.metadata.get('maps_to_job_id', False):
                value = job_id
            if field.metadata.get('maps_to_decider_parameters', False) and decider_parameters is not None:
                value = decider_parameters
            value = self.preprocess_value(field.name, value)
            if field.metadata.get('is_input_file', False):
                value = FileLike.get_name(value, True)
            try:
                self.make_substitution(js, field, value)
            except Exception as ex:
                raise ValueError(f"Error when processing field {field.name}") from ex
        self.after_substitution(js)
        return js


    def get_input_files(self) -> list[FileLike.Type]:
        result = []
        for field in get_dataclass_fields(type(self)):
            if field.metadata.get('is_input_file', False):
                result.append(getattr(self, field.name))
        return result

    def as_brainbox_task(self):
        ordering_token_components = {}
        for field in get_dataclass_fields(type(self)):
            ordering = field.metadata.get('is_input_file', None)
            if ordering is not None:
                ordering_token_components[ordering] = str(getattr(self, field.name))
        ordering_token ='///'.join(ordering_token_components[k] for k in sorted(ordering_token_components))

        return BrainBoxTask(
            decider='ComfyUI',
            decider_method='run_workflow',
            arguments=dict(workflow=self),
            ordering_token=ordering_token
        )
