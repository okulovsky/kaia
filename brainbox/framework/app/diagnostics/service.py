from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from brainbox.framework.job_processing.core.job import Job
from brainbox.framework.controllers.architecture import ControllerRegistry, brainbox_file_like_to_bytes_iterable
from brainbox.framework.controllers.self_test.last_call import LastCallDocumentation, ValueDocumentation
from foundation_kaia.marshalling_2 import File
from foundation_kaia.marshalling_2.marshalling.model.file_like import FileLikeHandler
from brainbox.framework.common import DeciderModel
from .interface import IDiagnosticsService
from ...job_processing.main_loop import MainLoop
from brainbox.framework.job_processing import OperatorLogItem



class DiagnosticsService(IDiagnosticsService):
    def __init__(self, engine, cache_folder: Path, loop: MainLoop):
        self.engine = engine
        self.cache_folder = cache_folder
        self.loop = loop

    def last_call(self) -> LastCallDocumentation:
        with Session(self.engine) as session:
            job = session.scalar(select(Job).order_by(Job.received_timestamp.desc()))
        if job is None:
            raise ValueError("No jobs found")

        api_class = ControllerRegistry.discover().get_api_class(job.decider)
        if api_class is None:
            raise ValueError(f"Cannot find api class for decider {job.decider!r}")
        decider_model = DeciderModel.parse(api_class)
        method = decider_model.methods.get(job.method or '')
        if method is None:
            raise ValueError(f"Cannot find endpoint for {job.decider}::{job.method}")

        def _to_value_doc(name: str, value: Any) -> ValueDocumentation:
            if name in method.file_argument_names:
                try:
                    content = b''.join(brainbox_file_like_to_bytes_iterable(value, self.cache_folder))
                    return ValueDocumentation(json=None, file=File(FileLikeHandler.guess_name(value), content))
                except Exception as e:
                    return ValueDocumentation(json=None, file=None, error=str(e))
            if isinstance(value, (dict, list, str, float, int, bool, type(None))):
                return ValueDocumentation(json=value, file=None)
            return ValueDocumentation(json=repr(value), file=None)

        def _result_to_value_doc(value: Any) -> ValueDocumentation:
            if method.result_is_file:
                try:
                    content = b''.join(brainbox_file_like_to_bytes_iterable(value, self.cache_folder))
                    return ValueDocumentation(json=None, file=File(FileLikeHandler.guess_name(value), content))
                except Exception as e:
                    return ValueDocumentation(json=None, file=None, error=str(e))
            if isinstance(value, (dict, list, str, float, int, bool, type(None))):
                return ValueDocumentation(json=value, file=None)
            return ValueDocumentation(json=repr(value), file=None)

        return LastCallDocumentation(
            decider=job.decider,
            parameter=job.parameter,
            method=job.method,
            arguments={name: _to_value_doc(name, val) for name, val in job.arguments.items()},
            result=_result_to_value_doc(job.result) if job.success else None,
            log=tuple(job.log) if job.log else (),
            error=job.error,
        )

    def operator_log(self, entries_count: int | None = 100) -> list[OperatorLogItem]:
        items = self.loop.core.operator_log.log_items
        if entries_count is not None:
            items = items[-entries_count:]
        return items
