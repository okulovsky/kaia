"""Compatibility alias for the canonical wakeword implementation."""

import importlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brainbox.deciders.voice_analysis.wakeword_training.runtime.settings import *

sys.modules[__name__] = importlib.import_module(
    "brainbox.deciders.voice_analysis.wakeword_training.runtime.settings"
)
