"""Explicit preparation, separate from generation and training."""

import subprocess
import sys
from pathlib import Path


def training_ready(api):
    from brainbox.deciders import WakewordTraining

    statuses = {s.name: s for s in api.controllers.status().controllers}
    status = statuses.get("WakewordTraining")
    if status is None:
        return {
            "ready": False,
            "reason": "WakewordTraining not registered: update server code and restart BrainBox",
        }
    if not status.installed:
        return {"ready": False, "reason": "WakewordTraining image missing; run prepare"}
    return api.execute(WakewordTraining.new_task().readiness())


def prepare_training(api, check_only=False):
    from brainbox.deciders import WakewordTraining

    readiness = training_ready(api)
    if readiness["ready"] or check_only:
        return readiness
    statuses = {s.name: s for s in api.controllers.status().controllers}
    if "WakewordTraining" not in statuses:
        raise RuntimeError(readiness["reason"])
    if not statuses["WakewordTraining"].installed:
        key = api.controllers.install.start("WakewordTraining")
        for item in api.controllers.install.follow_report(key):
            print(item, flush=True)
        api.controllers.install.join(key)
    api.execute(WakewordTraining.new_task().install())
    return training_ready(api)


def prepare_generation(api, config, check_only=False):
    if not check_only:
        code = "from chara.wakeword.generation.dependencies import issues; import sys; sys.exit(10 if issues() else 0)"
        result = subprocess.run([sys.executable, "-c", code], check=False)
        if result.returncode == 10:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    "-r",
                    str(Path(__file__).parent / "requirements-host.lock.txt"),
                ],
                check=True,
            )
        elif result.returncode:
            raise RuntimeError("generation preflight failed")
    from .generation.environment import check, ready, setup, show
    from .generation.settings import GenerationSettings

    settings = GenerationSettings.read(config)
    if not check_only:
        setup(api, settings)
    rows = check(api, settings)
    show(rows)
    return {"ready": ready(rows)}
