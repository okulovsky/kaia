from abc import ABC, abstractmethod
from datetime import datetime


class ILoader(ABC):
    """
    Source of truth for which files exist, and for each file's content and
    modification time (e.g. Google Drive). CreativeArticulatorData decides
    whether a file's cache is stale by calling get_modified() first (cheap:
    metadata only) and only calls get_text() (the actual content fetch) for
    ids that turn out to need it.
    """

    @abstractmethod
    def get_ids(self) -> list[str]:
        """
        The ids of every file that currently exists in the source. This is
        what defines the set of files the tree covers: synchronize() asks the
        loader for it rather than being told from outside, so a file that
        appeared or disappeared in the source is picked up on the next
        synchronization without anyone having to notice and report it.
        """

    @abstractmethod
    def get_modified(self, id: str) -> datetime:
        pass

    @abstractmethod
    def get_text(self, id: str) -> str:
        pass
