from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable
from ...common import ApiCallback
from ...common.streaming import StreamingStorage
from ..architecture import brainbox_file_like_to_bytes_iterable
import json

from foundation_kaia.marshalling import FileLikeHandler, ApiCall, ResultType, SerializationContext, CallModel
from brainbox.framework.common.decider_model import DeciderMethodModel
from foundation_kaia.brainbox_utils import BrainboxReportItem
import uuid

if TYPE_CHECKING:
    from ..docker_web_service_controller import DockerWebServiceApi


@dataclass
class FileDetails:
    filename: str
    access: str
    is_streaming: bool


class DockerMarshallingApiCall:
    def __init__(self, api: DockerWebServiceApi, call: ApiCall, decider_method: DeciderMethodModel):
        self.api = api
        self.call = call
        self.decider_method = decider_method

    @property
    def endpoint(self):
        return self.call.endpoint

    def file_required(self) -> bool:
        return self.endpoint.result.type in (ResultType.BinaryFile, ResultType.StringIterable, ResultType.CustomIterable)

    def _get_file_details(self, current_job_id: str) -> FileDetails | None:
        output_name = f'{current_job_id}.{self.endpoint.service_model.name}.{self.endpoint.signature.name}.{uuid.uuid4()}'
        if self.endpoint.result.type == ResultType.BinaryFile:
            return FileDetails(output_name + self.endpoint.result.guess_extension(), 'wb', True)
        elif self.endpoint.result.type == ResultType.StringIterable:
            return FileDetails(output_name + '.txt', 'wb', True)
        elif self.endpoint.result.type == ResultType.CustomIterable:
            if self.endpoint.result.serializer.annotation.is_single_type(bytes):
                return FileDetails(output_name + self.endpoint.result.guess_extension(), 'wb', True)
            else:
                return FileDetails(output_name + '.jsonl', 'wb', True)
        else:
            return None

    def _previews(self, enumerable, name):
        for obj in enumerable:
            yield obj

    def write_to_file(self, result, write: Callable[[bytes], None], api_callback: ApiCallback):
        if self.endpoint.result.type == ResultType.BinaryFile:
            for chunk in self._previews(FileLikeHandler.to_bytes_iterable(result), 'bytes iterable'):
                write(chunk)
        elif self.endpoint.result.type == ResultType.StringIterable:
            for line in self._previews(result, 'string iterable'):
                write((line + '\n').encode('utf-8'))
        elif self.endpoint.result.type == ResultType.CustomIterable:
            ctx = SerializationContext()
            for obj in self._previews(result, 'custom_iterable'):
                if isinstance(obj, BrainboxReportItem):
                    if obj.log is not None:
                        api_callback.log(obj.log)
                    if obj.progress is not None:
                        api_callback.report_progress(obj.progress)
                write((json.dumps(self.endpoint.result.serializer.to_json(obj, ctx)) + '\n').encode('utf-8'))
        else:
            raise ValueError("Should not be here: only files and streams should end in this method")

    def postprocess(self, result):
        if not self.file_required():
            return result
        details = self._get_file_details(self.api.current_job_id)
        storage = StreamingStorage(self.api.cache_folder)
        committed = False
        storage.begin_writing(details.filename)
        try:
            if details.is_streaming:
                self.api.context.api_callback.report_responding(details.filename)
            self.write_to_file(
                result,
                lambda data: storage.append(details.filename, data),
                self.api.context.api_callback
            )
            committed = True
            storage.commit(details.filename)
        finally:
            if not committed:
                storage.delete(details.filename)
        return details.filename

    def preprocess(self, *args, **kwargs) -> CallModel:
        values = self.endpoint.signature.assign_parameters_to_names(*args, **kwargs)
        for name, v in values.items():
            if name in self.decider_method.file_argument_names:
                values[name] = brainbox_file_like_to_bytes_iterable(v, self.api.cache_folder)
        model = self.call.create_content_model(**values)
        return model

    def __call__(self, *args, **kwargs):
        model = self.preprocess(*args, **kwargs)
        model.base_url = 'http://' + self.api.address
        result = self.call.make_call(model)
        return self.postprocess(result)

