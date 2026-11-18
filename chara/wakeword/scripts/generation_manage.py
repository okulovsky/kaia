"""Deprecated generation aliases."""

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from chara.wakeword.scripts.manage import main

if __name__ == "__main__":
    raise SystemExit(main())
