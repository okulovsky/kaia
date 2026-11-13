import hashlib

import yaml
from brainbox.deciders import ParlerTts, Vosk

from chara import Chara

from .io import write_json
from .local.resources import ResourceInstaller


def read_voice_models(settings):
    voice_models = {}
    for decider, name, model in (
        (ParlerTts, "ParlerTts", "mini-v1"),
        (Vosk, "Vosk", "en"),
    ):
        storage = Chara.Apis.brainbox_api.resources(decider)
        try:
            raw = storage.read("installation.yaml")
            installed = yaml.safe_load(raw) or {}
            if model not in installed:
                raise ValueError(f"{name} model {model} is not installed")
        except Exception as error:
            raise RuntimeError(
                f"resources: cannot verify {name}/{model}: {error}; check the BrainBox URL and install the model using its controller"
            ) from error
        voice_models[name] = {
            "model": model,
            "spec": installed[model],
            "installation_sha256": hashlib.sha256(raw).hexdigest(),
        }
    return voice_models


def prepare_resources(settings):
    voice_models = read_voice_models(settings)
    result = ResourceInstaller(settings.resource_folder).load(settings.resource_specs)
    if (
        not isinstance(result, dict)
        or not result.get("resources")
        or not result.get("versions")
    ):
        raise ValueError(
            "resources: incomplete local resource manifest; run make setup"
        )
    result["voice_models"] = voice_models
    write_json(Chara.current.folder / "resources.json", result)
    return result
