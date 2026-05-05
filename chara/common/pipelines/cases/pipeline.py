from .case import TCase
from .case_collection import CaseCollection
from typing import TypeAlias, Callable

ICasePipeline: TypeAlias = Callable[[CaseCollection[TCase]], CaseCollection[TCase]]
