"""Read-only readiness checks and idempotent setup through the running BrainBox."""

from dataclasses import dataclass

import yaml

REQUIRED = ("ParlerTts", "Vosk")


@dataclass
class Check:
    component: str
    state: str
    detail: str


def requirements():
    from dataclasses import asdict

    from brainbox.deciders import ParlerTts, Vosk

    spec = Vosk.Settings.models_to_install["en"]
    return {
        "ParlerTts": ("mini-v1", ParlerTts.Settings.models_to_install["mini-v1"]),
        "Vosk": ("en", asdict(spec)),
    }


def check(api, settings):
    """Read manifests/files only: do not dispatch jobs or start containers."""
    statuses = {s.name: s for s in api.controllers.status().controllers}
    rows = []
    required_models = requirements()
    for name in REQUIRED:
        status = statuses.get(name)
        if status is None:
            rows.append(
                Check(
                    name,
                    "blocked",
                    "not registered; update/restart the BrainBox server",
                )
            )
            continue
        rows.append(
            Check(
                name + "/image",
                "ready" if status.installed else "missing",
                "Docker image",
            )
        )
        storage = api.resources(name)
        installed = storage.is_file("installation.yaml")
        rows.append(
            Check(
                name + "/service",
                "ready" if installed else "missing",
                "installation manifest",
            )
        )
        if name in required_models:
            model, expected = required_models[name]
            manifest = (
                (yaml.safe_load(storage.read("installation.yaml")) or {})
                if installed
                else {}
            )
            state = (
                "missing"
                if model not in manifest
                else ("ready" if manifest[model] == expected else "blocked")
            )
            rows.append(
                Check(
                    name + "/" + model,
                    state,
                    "model specification"
                    if state != "blocked"
                    else "model specification differs; resolve manually",
                )
            )
    from .dependencies import issues

    problems = issues()
    rows.append(
        Check(
            "host/dependencies",
            "missing" if problems else "ready",
            "; ".join(problems) or "CPU processing dependencies and FFmpeg",
        )
    )
    from .local.resources import ResourceInstaller

    installer = ResourceInstaller(settings.resource_folder)
    if not (installer.root / "manifest.json").is_file():
        rows.append(
            Check(
                "host/resources", "missing", "run make setup to prepare local resources"
            )
        )
    else:
        try:
            installer.load(settings.resource_specs, verify=False)
            rows.append(
                Check(
                    "host/resources",
                    "ready",
                    "local manifest and files (full hashes validated on run)",
                )
            )
        except Exception as error:  # noqa: BLE001 - Pipeline boundary records failures from remote services and native libraries.
            state = (
                "missing"
                if any(
                    term in str(error)
                    for term in (
                        "configuration changed",
                        "incompatible local dependency",
                        "recipe versions",
                    )
                )
                else "blocked"
            )
            rows.append(Check("host/resources", state, str(error)))

    return rows


def ready(rows):
    return all(row.state == "ready" for row in rows)


def show(rows):
    for row in rows:
        print(f"{row.state.upper():8} {row.component:36} {row.detail}", flush=True)


def setup(api, settings):
    from brainbox.deciders import ParlerTts, Vosk

    entries = {"ParlerTts": ParlerTts, "Vosk": Vosk}
    rows = check(api, settings)
    show(rows)
    if any(row.state == "blocked" for row in rows):
        raise RuntimeError(
            "Resolve BLOCKED checks before setup; existing data will not be overwritten"
        )
    print(
        "Setup downloads missing images/models and full corpora (well over 25 GB on first use).",
        flush=True,
    )
    if any(r.component == "host/dependencies" and r.state != "ready" for r in rows):
        raise RuntimeError("Install host dependencies before preparing resources")
    for name in REQUIRED:
        entry = entries[name]
        if any(r.component == name + "/image" and r.state == "missing" for r in rows):
            print(
                "Installing "
                + name
                + " using server settings (Vosk may include en/de/ru).",
                flush=True,
            )
            key = api.controllers.install.start(name)
            for item in api.controllers.install.follow_report(key):
                print(item, flush=True)
            api.controllers.install.join(key)
            status = {s.name: s for s in api.controllers.status().controllers}
            if not status[name].installed:
                raise RuntimeError("Image installation failed: " + name)
        storage = api.resources(name)
        if not storage.is_file("installation.yaml"):
            print("Initializing " + name, flush=True)
            api.execute(entry.new_task().install())
        if name in requirements():
            model, expected = requirements()[name]
            manifest = yaml.safe_load(storage.read("installation.yaml")) or {}
            if model not in manifest:
                print("Downloading " + name + "/" + model, flush=True)
                spec = entry.Settings.models_to_install[model]
                api.execute(entry.new_task().download_model(model, spec))
            elif manifest[model] != expected:
                raise RuntimeError("Model specification differs: " + name + "/" + model)
    print("Preparing and validating local resources...", flush=True)
    from .local.resources import ResourceInstaller

    ResourceInstaller(settings.resource_folder).prepare(settings.resource_specs)
    final = check(api, settings)
    show(final)
    if not ready(final):
        raise RuntimeError("Setup did not complete; see checks above")
