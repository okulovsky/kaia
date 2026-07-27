from typing import Any, Callable
from chara import CaseCollection, Chara, logger
from chara.common.tools.drawing import Drawer, Img
from .package_pipeline import PackagePipeline
from .dto import ImageSetupStatistics
from ..activity import ImageRequest, ImageSetup
from ..scenario import IImageScenario
from ..drawing import DrawingCase
from .image_statistics_pipeline import ImageStatisticsPipeline
from .balancing_requests import balancing_requests
from pathlib import Path


DEFAULT_STRATIFICATION_FIELDS = ('character_name', 'season', 'weather', 'time_of_day', 'special_day')


class GenerationPipeline:
    def __init__(self,
                 activities_file: Path,
                 images_budget: int,
                 scenario_pipeline: Callable[[list[ImageRequest]], CaseCollection[IImageScenario]],
                 drawing_pipeline: Callable[[CaseCollection[IImageScenario]], CaseCollection[DrawingCase]],
                 report_groups: tuple[Callable[[DrawingCase], Any], ...] = (),
                 stratification_fields: tuple[str, ...] = DEFAULT_STRATIFICATION_FIELDS,
                 ):
        self.activities_file = activities_file
        self.images_budget = images_budget
        self.scenario_pipeline = scenario_pipeline
        self.drawing_pipeline = drawing_pipeline
        self.report_groups = report_groups
        self.stratification_fields = stratification_fields

    def __call__(self, setups: list[ImageSetup]):
        # Captured before any nested Chara.call() pushes its own subfolder, so the
        # reports land next to this run's result.pickle, not inside a "reports" subfolder.
        folder = Chara.current.folder

        statistics_pipeline = ImageStatisticsPipeline(self.activities_file)

        statistics_before = Chara.call(statistics_pipeline, 'statistics_before')(setups)
        self._log_stratification_statistics('Coverage before the run', statistics_before)
        self._log_activity_statistics('Activities before the run', statistics_before)

        @Chara.phase
        def select_requests():
            return balancing_requests(statistics_before, self.images_budget, self.stratification_fields)

        requests = Chara.previous.result
        scenarios = Chara.call(self.scenario_pipeline)(requests).successes_collection
        drawings = Chara.call(self.drawing_pipeline)(scenarios)
        package_pipeline = PackagePipeline()
        Chara.call(package_pipeline)(drawings)
        Chara.call(self._write_reports, 'reports')(folder, drawings)

        # Recollected from scratch rather than incrementally updated from `statistics_before` -
        # simpler, and correct even if a previous run was interrupted partway through.
        statistics_after = Chara.call(statistics_pipeline, 'statistics_after')(setups)
        self._log_stratification_statistics('Coverage after the run', statistics_after)
        self._log_activity_statistics('Activities after the run', statistics_after)

    def _log_stratification_statistics(self, label: str, statistics: list[ImageSetupStatistics]) -> None:
        totals: dict[tuple, int] = {}
        available: dict[tuple, int] = {}
        for stat in statistics:
            key = stat.setup.to_fingerprint().stratification_key(self.stratification_fields)
            total = sum(activity.generated for activity in stat.activity_status.values())
            totals[key] = totals.get(key, 0) + total
            available[key] = available.get(key, 0) + len(stat.activity_status)

        # A group with no catalog activities at all (e.g. outside the activity
        # catalog's lookahead window) can never be picked by balancing_requests,
        # no matter the budget - it's not "pending", it's delayed until the
        # catalog catches up to it.
        delayed = sum(1 for key in totals if available[key] == 0)
        due = len(totals) - delayed

        histogram: dict[int, int] = {}
        for key, total in totals.items():
            if available[key] == 0:
                continue
            histogram[total] = histogram.get(total, 0) + 1

        logger.info(f"{label} ({self.stratification_fields} groups):")
        logger.info(f"  {len(totals)} group(s) total")
        logger.info(f"  {delayed} delayed (no catalog activities yet)")
        logger.info(f"  {due} due")
        for image_count in sorted(histogram):
            count = histogram[image_count]
            percentage = 100 * count / due if due else 0
            logger.info(f"  {image_count} image(s): {count} group(s) ({percentage:.0f}%)")

    def _log_activity_statistics(self, label: str, statistics: list[ImageSetupStatistics]) -> None:
        # Same groups, same delayed/due split as _log_stratification_statistics -
        # but histogrammed by how many distinct activities a group has at least one
        # image for, rather than by its raw image count (a single activity can have
        # several images, which the image-count histogram can't tell apart from
        # several distinct activities with one image each).
        available: dict[tuple, int] = {}
        represented: dict[tuple, int] = {}
        for stat in statistics:
            key = stat.setup.to_fingerprint().stratification_key(self.stratification_fields)
            available[key] = available.get(key, 0) + len(stat.activity_status)
            represented[key] = represented.get(key, 0) + sum(
                1 for activity in stat.activity_status.values() if activity.generated > 0
            )

        delayed = sum(1 for count in available.values() if count == 0)
        due = len(available) - delayed

        histogram: dict[int, int] = {}
        for key, count in represented.items():
            if available[key] == 0:
                continue
            histogram[count] = histogram.get(count, 0) + 1

        logger.info(f"{label} ({self.stratification_fields} groups by activities represented):")
        logger.info(f"  {len(available)} group(s) total")
        logger.info(f"  {delayed} delayed (no catalog activities yet)")
        logger.info(f"  {due} due")
        for activity_count in sorted(histogram):
            count = histogram[activity_count]
            percentage = 100 * count / due if due else 0
            logger.info(f"  {activity_count} activity(ies): {count} group(s) ({percentage:.0f}%)")

    def _write_reports(self, folder: Path, drawings: CaseCollection[DrawingCase]) -> None:
        cases = drawings.successes
        self._write_overview_report(folder, cases)
        self._write_variants_report(folder, cases)

    def _write_overview_report(self, folder: Path, cases: list[DrawingCase]) -> None:
        drawer = Drawer(cases, lambda c: Img(c.image).resize(400))
        for group in self.report_groups:
            drawer = drawer.group(group)
        html = f'<html><body>{drawer.tiles(4).to_html()}</body></html>'
        (folder / 'report_by_group.html').write_text(html)

    def _write_variants_report(self, folder: Path, cases: list[DrawingCase]) -> None:
        items = []
        for case in cases:
            if not case.variants:
                continue
            items.append((case, 'main', case.image))
            for key, variant in case.variants.items():
                if variant.image is not None:
                    items.append((case, key, variant.image))

        if not items:
            return

        drawer = Drawer(items, lambda item: Img(item[2]).resize(400))
        drawer = drawer.tiles(lambda item: item[1], lambda item: item[0].image.stem)
        html = f'<html><body>{drawer.to_html()}</body></html>'
        (folder / 'report_variants.html').write_text(html)


