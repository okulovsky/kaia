import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    from brainbox.deciders import Vosk
    from brainbox.deciders.voice_analysis.vosk.app import interface as vosk_interface
    from foundation_kaia.brainbox_utils import IInstallingSupport  # noqa: F401 - Import probes availability of this optional runtime API.
    from foundation_kaia.marshalling.protocol.model.service_model import ServiceModel  # noqa: F401 - Import probes availability of this optional runtime API.
except ImportError:
    Vosk = None


@unittest.skipIf(Vosk is None, "requires the kaia environment")
class NativeContractsTests(unittest.TestCase):
    def load_service(self, which, interface, aliases):
        path = (
            Path(__file__).resolve().parents[3]
            / "brainbox/deciders/voice_analysis"
            / which
            / "app/service.py"
        )
        spec = importlib.util.spec_from_file_location("tested_" + which, path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, dict(interface=interface, **aliases)):
            spec.loader.exec_module(module)
        return module

    def test_empty_vosk_parts_are_expected_not_key_errors(self):
        module = self.load_service(
            "vosk", vosk_interface, {"vosk": SimpleNamespace(KaldiRecognizer=object)}
        )
        service = module.VoskService(None)
        service.transcribe = lambda file, model: [
            {"text": ""},
            {"text": "hi", "result": [{"word": "hi"}]},
        ]
        self.assertEqual(service.transcribe_to_array("unused"), [{"word": "hi"}])
        service.transcribe = lambda file, model: [{"text": ""}]
        self.assertEqual(service.transcribe_to_array("unused"), [])
