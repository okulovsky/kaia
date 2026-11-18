"""Compatibility alias for the canonical wakeword implementation."""

import importlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chara.wakeword.generation_pipeline import *

sys.modules[__name__] = importlib.import_module("chara.wakeword.generation_pipeline")
