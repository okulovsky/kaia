import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from training_fixtures import dataset_fixture

from brainbox.deciders.voice_analysis.wakeword_training.runtime.execution import (
    run_training,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.reporting import (
    key_metrics_section,
    render_training_report,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.settings import (
    TrainingSettings,
)
from chara.wakeword.generation.io import read_json, sha256


class MetricLabels(HTMLParser):
    def __init__(self):
        super().__init__()
        self.labels = []
        self.names = []
        self.values = []
        self.collect = None

    def handle_starttag(self, tag, attrs):
        if tag == "th":
            self.collect = self.labels
        elif tag == "h3":
            self.collect = self.names
        elif tag == "p" and dict(attrs).get("class") == "metric-value":
            self.collect = self.values

    def handle_endtag(self, tag):
        if tag in ("th", "h3", "p"):
            self.collect = None

    def handle_data(self, data):
        if self.collect is not None:
            self.collect.append(data)


class ReportTests(unittest.TestCase):
    def test_key_metrics_show_recall_instead_of_precision(self):
        metrics = {
            "supervised": {"recall": 0.75, "precision": None},
            "background": {"threshold_windows_per_feature_hour": 1.25},
            "unavailable_values": {"precision": "TP+FP=0"},
        }
        for ru in (False, True):
            document = key_metrics_section(metrics, ru)
            labels = MetricLabels()
            labels.feed(document)
            self.assertEqual(labels.names, ["recall", "FA/h"])
            self.assertEqual(labels.values, ["0.75", "1.25"])
            self.assertIn("TP / (TP + FN)", document)

    def test_offline_report_and_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = dataset_fixture(root / "source")
            output = root / "out"
            result = run_training(data, TrainingSettings(), output)
            self.assertEqual(result.status, "complete", result.error)
            text = result.report.read_text(encoding="utf-8")
            self.assertLess(
                text.index('id="validation_metrics"'),
                text.index('id="training_history"'),
            )
            self.assertLess(
                text.index('id="training_history"'),
                text.index('id="dataset_description"'),
            )
            self.assertIn("<svg", text)
            metrics = read_json(output / "metrics.json")
            for filename in ("report.html", "report_ru.html"):
                document = (output / filename).read_text(encoding="utf-8")
                self.assertLess(
                    document.index('id="key_metrics"'),
                    document.index('id="validation_metrics"'),
                )
                labels = MetricLabels()
                labels.feed(document)
                self.assertEqual(labels.names, ["recall", "FA/h"])
                self.assertAlmostEqual(
                    float(labels.values[0]), metrics["supervised"]["recall"]
                )
                self.assertAlmostEqual(
                    float(labels.values[1]),
                    metrics["background"]["threshold_windows_per_feature_hour"],
                )
                self.assertTrue(set(metrics["supervised"]).issubset(labels.labels))
                self.assertTrue(set(metrics["background"]).issubset(labels.labels))
                self.assertNotIn("Полнота", document)
                self.assertNotIn("Точность положительных решений", document)
            before = sha256(output / "history.jsonl")
            result.report.unlink()
            render_training_report(output)
            self.assertEqual(before, sha256(output / "history.jsonl"))
