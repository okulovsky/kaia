"""Publish ONNX only after checker, CPU execution and numerical parity."""

import os
from pathlib import Path
from uuid import uuid4

import numpy as np
import onnx
import onnxruntime as ort
import torch

from ..generation.io import sha256
from .dependencies import versions
from .metrics import valid_scores
from .model import ProbabilityModel


def cpu_session(path, threads=2):
    options = ort.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    return ort.InferenceSession(
        str(path), sess_options=options, providers=["CPUExecutionProvider"]
    )


def export_model(model, path, sample, settings, parity_batches=None):
    path = Path(path)
    temp = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    model = model.to("cpu").eval()
    wrapped = ProbabilityModel(model).eval()
    sample = np.asarray(sample, dtype=np.float32)
    if len(sample) < 2:
        sample = np.concatenate([sample, sample])
    maximum = 0.0
    try:
        torch.onnx.export(
            wrapped,
            torch.from_numpy(sample[:1]),
            str(temp),
            opset_version=14,
            input_names=["onnx::Flatten_0"],
            output_names=["output"],
            dynamic_axes={"onnx::Flatten_0": {0: "batch"}, "output": {0: "batch"}},
        )
        onnx.checker.check_model(str(temp))
        session = cpu_session(temp, settings.num_threads)
        from itertools import chain

        for batch in chain((sample[:1], sample), parity_batches or ()):
            with torch.no_grad():
                reference = wrapped(torch.from_numpy(batch)).numpy()
            exported = session.run(["output"], {"onnx::Flatten_0": batch})[0]
            if exported.shape != (len(batch), 1):
                raise ValueError("ONNX output shape mismatch")
            valid_scores(exported.reshape(-1))
            maximum = max(maximum, float(np.max(np.abs(reference - exported))))
            if not np.allclose(
                reference,
                exported,
                atol=settings.export_atol,
                rtol=settings.export_rtol,
            ):
                raise ValueError("ONNX parity failure")
        del session
        os.replace(temp, path)
        return {
            "opset": 14,
            "input_name": "onnx::Flatten_0",
            "output_name": "output",
            "input_dtype": "float32",
            "input_shape": ["B", 16, 96],
            "output_shape": ["B", 1],
            "sigmoid_included": True,
            "structural_check": True,
            "cpu_execution": True,
            "batch_sizes": [1, len(sample)],
            "parity_passed": True,
            "max_absolute_error": maximum,
            "tolerance": {"atol": settings.export_atol, "rtol": settings.export_rtol},
            "model_sha256": sha256(path),
            "package_versions": versions(),
        }
    finally:
        temp.unlink(missing_ok=True)
