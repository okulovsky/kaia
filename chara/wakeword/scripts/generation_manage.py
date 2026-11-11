"""Manage wakeword prerequisites through BrainBox: check, setup, run."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Also support direct invocation from Make without requiring editable installation.
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "setup", "run"))
    parser.add_argument(
        "--brainbox-url",
        default=os.environ.get("CHARA_BRAINBOX_URL", "http://127.0.0.1:8090"),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "learn-settings.json",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "run" and args.output is None:
        parser.error("run requires --output")
    os.environ["CHARA_BRAINBOX_URL"] = args.brainbox_url
    try:
        if args.command == "setup":
            # Imports used by readiness checks can lock native extensions on Windows.
            # Finish the entire preflight process before pip replaces any packages.
            preflight = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from pathlib import Path; import sys; "
                        "sys.path.insert(0, sys.argv[1]); "
                        "from chara.wakeword import GenerationSettings; "
                        "from chara.wakeword.generation.local.resources import ResourceInstaller; "
                        "from chara.wakeword.generation.dependencies import issues; "
                        "settings = GenerationSettings.read(Path(sys.argv[2])).validate(); "
                        "ResourceInstaller(settings.resource_folder).check_space(settings.resource_specs); "
                        "sys.exit(10 if issues() else 0)"
                    ),
                    str(ROOT),
                    str(args.config.resolve()),
                ],
                check=False,
            )
            if preflight.returncode not in (0, 10):
                raise RuntimeError("Setup preflight failed; see the error above")
            if preflight.returncode == 10:
                lock = (
                    Path(__file__).resolve().parents[1] / "requirements-host.lock.txt"
                )
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--no-deps",
                        "--prefer-binary",
                        "-r",
                        str(lock),
                    ],
                    check=True,
                )
        from brainbox import BrainBox

        from chara.wakeword import GenerationSettings
        from chara.wakeword.generation.environment import check, ready, setup, show

        settings = GenerationSettings.read(args.config)
        settings.validate()
        api = BrainBox.Api(args.brainbox_url)
        try:
            api.wait_for_connection(3)
        except Exception as error:
            raise RuntimeError(
                f'BrainBox unavailable at {args.brainbox_url}. Start it from the kaia root in another terminal: python -m brainbox.run --data-folder "D:/brainbox-data". For a remote server, start it on that host.'
            ) from error
        if args.command == "setup":
            setup(api, settings)
            return 0
        rows = check(api, settings)
        show(rows)
        if not ready(rows):
            print(
                "Not ready. Run make setup with the same BRAINBOX_URL and CONFIG.",
                file=sys.stderr,
            )
            return 1
        if args.command == "run":
            from chara.wakeword import run

            result = run(settings, args.output)
            return 0 if result.status == "complete" else 1
        return 0
    except Exception as error:  # noqa: BLE001 - Pipeline boundary records failures from remote services and native libraries.
        print(f"{args.command} failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
