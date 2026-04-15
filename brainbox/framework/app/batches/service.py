from __future__ import annotations
from collections import defaultdict
from sqlalchemy import select, func, case, and_, Float
from sqlalchemy.orm import Session
from brainbox.framework.job_processing.core.job import Job
from brainbox.framework.job_processing.main_loop import CancelAction, CommandQueue
from .dto import Batches, BatchSummary
from .interface import IBatchesService


class BatchesService(IBatchesService):
    def __init__(self, engine, command_queue: CommandQueue):
        self.engine = engine
        self.command_queue = command_queue

    def _get_ordered_batch_ids(self, session) -> list[str]:
        return list(session.execute(
            select(Job.batch)
            .group_by(Job.batch)
            .order_by(func.min(Job.received_timestamp).desc())
        ).scalars().all())

    def _get_batch_stats(self, session, batch_ids: list[str]) -> tuple[dict, dict[str, list[str]]]:
        # Per-batch aggregates
        agg_rows = session.execute(
            select(
                Job.batch,
                func.count(Job.id).label('tasks_total'),
                func.sum(case((Job.success == True, 1), else_=0)).label('tasks_success'),
                func.sum(case(
                    (and_(Job.finished_timestamp.is_not(None), Job.success == False), 1), else_=0
                )).label('tasks_failure'),
                func.sum(case(
                    (and_(Job.accepted_timestamp.is_not(None), Job.finished_timestamp.is_(None)), 1), else_=0
                )).label('tasks_in_work'),
                func.sum(case(
                    (Job.accepted_timestamp.is_(None), 1), else_=0
                )).label('tasks_waiting'),
                func.min(Job.received_timestamp).label('received_timestamp'),
                func.max(Job.finished_timestamp).label('max_finished_timestamp'),
                func.sum(case(
                    (and_(
                        Job.finished_timestamp.is_not(None),
                        Job.accepted_timestamp.is_not(None),
                    ), (func.julianday(Job.finished_timestamp) -
                        func.julianday(Job.accepted_timestamp)) * 86400),
                    else_=0.0
                )).label('total_processing_time'),
            )
            .where(Job.batch.in_(batch_ids))
            .group_by(Job.batch)
        ).all()
        stats = {r.batch: r for r in agg_rows}

        # Per-(batch, decider, method) for human-readable names
        decider_rows = session.execute(
            select(Job.batch, Job.decider, Job.method, func.count(Job.id).label('n'))
            .where(Job.batch.in_(batch_ids))
            .group_by(Job.batch, Job.decider, Job.method)
        ).all()
        deciders: dict[str, list[str]] = defaultdict(list)
        for r in decider_rows:
            key = f"{r.decider}:{r.method}" if r.method else r.decider
            deciders[r.batch].append(f"{key} x {r.n}")

        return stats, dict(deciders)

    def _get_batch_progress(self, session, batch_ids: list[str]) -> dict[str, float]:
        rows = session.execute(
            select(
                Job.batch,
                func.avg(case(
                    (Job.finished_timestamp.is_not(None), 1.0),
                    (and_(
                        Job.accepted_timestamp.is_not(None),
                        Job.finished_timestamp.is_(None),
                    ), func.coalesce(Job.progress, 0.0)),
                    else_=0.0
                )).label('progress')
            )
            .where(Job.batch.in_(batch_ids))
            .group_by(Job.batch)
        ).all()
        return {r.batch: float(r.progress or 0.0) for r in rows}

    def get_batches(self, offset: int | None = None, size: int | None = None) -> Batches:
        with Session(self.engine) as session:
            all_ids = self._get_ordered_batch_ids(session)
            total = len(all_ids)

            start = offset or 0
            page_ids = all_ids[start: start + (size or 20)]

            if not page_ids:
                return Batches(items=[], total=total)

            stats, deciders = self._get_batch_stats(session, page_ids)
            progress = self._get_batch_progress(session, page_ids)

        summaries = []
        for batch_id in page_ids:
            row = stats[batch_id]
            tasks_finished = row.tasks_success + row.tasks_failure
            is_finished = tasks_finished == row.tasks_total

            summaries.append(BatchSummary(
                batch_id=batch_id,
                deciders=deciders.get(batch_id, []),
                received_timestamp=row.received_timestamp,
                finished_timestamp=row.max_finished_timestamp if is_finished else None,
                total_processing_time=float(row.total_processing_time) if is_finished else None,
                progress=progress.get(batch_id, 0.0),
                tasks_waiting=row.tasks_waiting,
                tasks_in_work=row.tasks_in_work,
                tasks_success=row.tasks_success,
                tasks_failure=row.tasks_failure,
                tasks_total=row.tasks_total,
                is_finished=is_finished,
            ))

        return Batches(items=summaries, total=total)

    def cancel_batch(self, batch_id: str) -> None:
        self.command_queue.put_action(CancelAction(None, batch_id))

    def get_batch_progress(self, batch_id: str) -> BatchSummary:
        with Session(self.engine) as session:
            stats, deciders = self._get_batch_stats(session, [batch_id])
            progress = self._get_batch_progress(session, [batch_id])
        row = stats[batch_id]
        tasks_finished = row.tasks_success + row.tasks_failure
        is_finished = tasks_finished == row.tasks_total
        return BatchSummary(
            batch_id=batch_id,
            deciders=deciders.get(batch_id, []),
            received_timestamp=row.received_timestamp,
            finished_timestamp=row.max_finished_timestamp if is_finished else None,
            total_processing_time=float(row.total_processing_time) if is_finished else None,
            progress=progress.get(batch_id, 0.0),
            tasks_waiting=row.tasks_waiting,
            tasks_in_work=row.tasks_in_work,
            tasks_success=row.tasks_success,
            tasks_failure=row.tasks_failure,
            tasks_total=row.tasks_total,
            is_finished=is_finished,
        )
