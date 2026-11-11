"""Local preflight; no remote model or audio dependency checks."""

import importlib
from importlib.metadata import PackageNotFoundError, version

PACKAGES = {
    "numpy": "1.26.4",
    "torch": "2.2.2+cpu",
    "onnx": "1.16.1",
    "onnxruntime": "1.17.3",
    "matplotlib": "3.9.2",
}


def issues(report_only=False):
    result = []
    for name, expected in PACKAGES.items():
        if report_only and name not in ("numpy", "matplotlib"):
            continue
        try:
            actual = version(name)
            compatible = (
                actual.split("+")[0] == "2.2.2"
                if name == "torch"
                else actual == expected
            )
            if not compatible:
                result.append(f"{name}: expected {expected}, installed {actual}")
            importlib.import_module(name)
        except (PackageNotFoundError, ImportError, OSError) as error:
            result.append(f"{name}: {error}")
    return result


def resolve_device(requested):
    import torch

    if requested == "cuda" and not torch.cuda.is_available():
        raise ValueError("requested cuda is unavailable")
    return (
        "cuda" if requested in ("cuda", "auto") and torch.cuda.is_available() else "cpu"
    )


def versions():
    import platform

    return dict(
        python=platform.python_version(),
        platform=platform.platform(),
        **{k: version(k) for k in PACKAGES},
    )
