"""Self-contained report rendered only from verified saved measurements."""

import html
from io import StringIO
from pathlib import Path

import numpy as np

from ..generation.io import read_json, sha256, write_json
from .metrics import calculate_metrics
from .state import history, run_lock, verify_hashes


def verified_sources(root):
    root = Path(root)
    marker = root / "manifest.json"
    if marker.exists():
        verify_hashes(root, read_json(marker)["hashes"], allow_missing_report=True)
    else:
        state = read_json(root / "state.json")
        for stage in ("training", "selecting", "exporting", "evaluating"):
            if stage not in state["completed_stages"]:
                raise ValueError(f"report requires completed {stage}")
            verify_hashes(root, state["completed_stages"][stage])
    snapshot = read_json(root / "data-snapshot.json")
    metrics = read_json(root / "metrics.json")
    settings = read_json(root / "config.json")
    model = root / (settings["model_name"] + ".onnx")
    if (
        sha256(model) != metrics["model_sha256"]
        or sha256(root / "data-snapshot.json") != metrics["dataset_snapshot_sha256"]
    ):
        raise ValueError("report model/snapshot identity mismatch")
    loaded = []
    try:
        for name in (
            "positive_validation",
            "negative_validation",
            "background_validation",
        ):
            item = metrics["scores_artifacts"][name]
            path = root / item["path"]
            if (
                not path.resolve().is_relative_to(root.resolve())
                or sha256(path) != item["sha256"]
            ):
                raise ValueError("saved scores hash mismatch")
            array = np.load(path, mmap_mode="r", allow_pickle=False)
            loaded.append(array)
            expected = (
                snapshot["background"]["total_valid_windows"]
                if name == "background_validation"
                else snapshot["supervised_parts"][
                    name.replace("_validation", "_features_test")
                ]["rows"]
            )
            if list(array.shape) != item["shape"] or len(array) != expected:
                raise ValueError("saved score shape mismatch")
        bg = snapshot["background"]
        calculated = calculate_metrics(
            *loaded,
            settings["threshold"],
            bg["evaluated_frames"],
            bg["frame_step_seconds"],
        )
        for key in calculated:
            if calculated[key] != metrics[key]:
                raise ValueError(f"saved metric mismatch: {key}")
    finally:
        for array in loaded:
            array._mmap.close()
    events = history(root)
    if not any(x["type"] == "update" for x in events):
        raise ValueError("report has no actual optimizer updates")
    return snapshot, metrics, settings, events


def write_report(root):
    root = Path(root)
    snapshot, metrics, settings, events = verified_sources(root)
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["svg.fonttype"] = "none"
    from matplotlib.figure import Figure

    figure = Figure(figsize=(10, 8), layout="constrained")
    axes = figure.subplots(3, 1)
    updates = [x for x in events if x["type"] == "update"]
    vals = [x for x in events if x["type"] == "validation"]
    for stage in (1, 2, 3):
        rows = [x for x in updates if x["stage"] == stage]
        axes[0].plot(
            [x["optimizer_update"] for x in rows],
            [x["weighted_bce_loss"] for x in rows],
            marker="o",
            markersize=3,
            label=f"Stage {stage}",
        )
    axes[0].set(ylabel="Weighted training BCE", xlabel="Actual optimizer update")
    axes[0].legend()
    for key in ("recall", "accuracy"):
        axes[1].plot(
            [x["optimizer_update"] for x in vals],
            [x[key] for x in vals],
            marker="o",
            label=key,
        )
    axes[1].set(ylabel="Validation fraction", xlabel="Actual optimizer update")
    axes[1].legend()
    axes[2].plot(
        [x["optimizer_update"] for x in vals],
        [x["window_fp_per_hour"] for x in vals],
        marker="o",
    )
    axes[2].set(
        ylabel="Threshold windows / feature hour", xlabel="Actual optimizer update"
    )
    svg = StringIO()
    figure.savefig(svg, format="svg", metadata={"Date": None})
    chart = svg.getvalue()
    chart = chart[chart.index("<svg") :]
    state = read_json(root / "state.json")

    def escaped(value):
        return html.escape(str(value))

    def table(values):
        return (
            "<table>"
            + "".join(
                "<tr><th>"
                + escaped(labels.get(k, k) if ru else k)
                + "</th><td>"
                + escaped(
                    (
                        "недоступно: не измерено"
                        if ru
                        else "unknown: "
                        + metrics["unavailable_values"].get(k, "not measured")
                    )
                    if v is None
                    else v
                )
                + "</td></tr>"
                for k, v in values.items()
            )
            + "</table>"
        )

    labels = {
        "positive_count": "Позитивных примеров",
        "negative_count": "Негативных примеров",
        "recall": "Полнота",
        "precision": "Точность положительных решений",
        "accuracy": "Доля верных решений",
        "positive_windows": "Положительных окон",
        "total_windows": "Всего окон",
        "feature_frames": "Кадров признаков",
        "frame_step_seconds": "Шаг кадра, с",
        "feature_equivalent_hours": "Эквивалентных часов признаков",
        "threshold_windows_per_feature_hour": "Пороговые окна/ч",
        "stride": "Шаг окна",
        "window_policy": "Правило окон",
        "waveform_hours": "Длительность аудио, ч",
        "threshold": "Порог",
    }
    summary = dict(metrics["supervised"])
    summary.update(metrics["background"])
    summary["threshold"] = metrics["threshold"]
    selection = read_json(root / "checkpoint-selection.json")
    for language in ("en", "ru"):
        ru = language == "ru"

        def tr(en, russian, ru=ru):
            return russian if ru else en

        body = f'<!doctype html><html lang="{language}"><meta charset="utf-8"><title>Wakeword</title><style>body{{font:16px system-ui;max-width:1100px;margin:2em auto;padding:1em}}td,th{{border:1px solid #ccc;padding:.4em;text-align:left}}table{{border-collapse:collapse}}svg{{max-width:100%;height:auto}}</style>'
        body += f"<h1>Wakeword: {escaped(settings['model_name'])}</h1><p>{escaped(settings['mode'])} · {escaped(state['run_id'])}</p>"
        body += (
            '<section id="validation_metrics"><h2>'
            + tr("Final model validation metrics", "Метрики валидации итоговой модели")
            + "</h2>"
        )
        body += "<p>ONNX SHA-256: " + escaped(metrics["model_sha256"]) + "</p>"
        body += (
            "<p>"
            + tr(
                "Background rate counts threshold-positive windows per feature-equivalent hour, not independent audio events. Stride: 1; windows stay within source segments. Validation was also used for checkpoint selection.",
                "Пороговые окна/ч — число превышений порога на фоне за эквивалентный час признаков, а не независимые события на аудио. Шаг: 1; окна не пересекают границы сегментов. Эта валидация также использовалась для отбора модели.",
            )
            + "</p>"
            + table(summary)
            + "</section>"
        )
        localized_chart = chart
        if ru:
            for en, russian in [
                ("Weighted training BCE", "Взвешенная BCE обучения"),
                ("Actual optimizer update", "Реальное обновление модели"),
                ("Validation fraction", "Доля на валидации"),
                ("Threshold windows / feature hour", "Пороговые окна / час признаков"),
                ("Stage ", "Стадия "),
                ("recall", "полнота"),
                ("accuracy", "доля верных решений"),
            ]:
                localized_chart = localized_chart.replace(en, russian)
        body += (
            '<section id="training_history"><h2>'
            + tr("Training curves", "Кривые обучения")
            + "</h2><p>"
            + tr(
                "Only actual updates and measurements are shown. Weighted training BCE is not validation loss.",
                "Показаны только реальные обновления и измерения. Взвешенная BCE обучения не является ошибкой валидации.",
            )
            + "</p>"
            + localized_chart
            + "</section>"
        )
        body += (
            '<section id="dataset_description"><h2>'
            + tr("Training and validation data", "Данные обучения и валидации")
            + "</h2>"
        )
        body += (
            "<table><tr><th>"
            + tr("Dataset part", "Часть датасета")
            + "</th><th>"
            + tr("Rows", "Строки")
            + "</th><th>"
            + tr("Shape", "Форма")
            + "</th></tr>"
        )
        for name, part in snapshot["supervised_parts"].items():
            body += (
                "<tr><td>"
                + escaped(name)
                + "</td><td>"
                + escaped(part["rows"])
                + "</td><td>"
                + escaped(part["actual_shape"])
                + "</td></tr>"
            )
        body += "</table>"
        bg = snapshot["background"]
        body += table(
            {
                tr("Background training shape", "Форма обучающего фона"): bg["train"][
                    "actual_shape"
                ],
                tr("Background windows evaluated", "Оценено фоновых окон"): bg[
                    "total_valid_windows"
                ],
                tr("Rejected samples", "Отбраковано записей"): snapshot["review_count"],
                tr("Target variants", "Варианты целевого слова"): snapshot[
                    "generation_settings"
                ].get("target_variants", []),
                tr("Background source", "Источник фона"): bg["provenance"].get(
                    "source", "unknown"
                ),
            }
        )
        body += (
            "</section><section><h2>"
            + tr(
                "Training settings and model selection",
                "Настройки обучения и отбор модели",
            )
            + "</h2>"
        )
        body += table(
            {
                tr("Seed", "Seed"): settings["seed"],
                tr("Stage iterations", "Итерации стадий"): settings["stage_steps"],
                tr("Learning rates", "Скорости обучения"): settings[
                    "stage_learning_rates"
                ],
                tr("Optimizer updates", "Обновления модели"): len(updates),
                tr("Selected checkpoints", "Отобрано checkpoints"): len(
                    selection["selected_ids"]
                ),
                tr("Fallback", "Резервный выбор"): selection.get("fallback_reason")
                or tr("not needed", "не потребовался"),
            }
        )
        body += "</section></html>"
        path = root / ("report_ru.html" if ru else "report.html")
        temporary = path.with_suffix(".html.tmp")
        temporary.write_text(body, encoding="utf-8")
        temporary.replace(path)
    path = root / "report.html"
    return path


def render_training_report(output):
    root = Path(output).resolve()
    with run_lock(root):
        path = write_report(root)
        marker = root / "manifest.json"
        if marker.exists():
            value = read_json(marker)
            value["hashes"]["report.html"] = sha256(path)
            value["hashes"]["report_ru.html"] = sha256(root / "report_ru.html")
            write_json(marker, value)
        return path
