import traceback
from dataclasses import dataclass, field
from ..parsers import IParser
from .applicator import IApplicator
from pathlib import Path
from yo_fluq import *
from .object_to_task import IObjectConverter, PromptBasedObjectConverter
from ..cache import JsonCacheManager, ICacheManager
from foundation_kaia.prompters import Address

T = TypeVar('T')

@dataclass
class BrainBoxMappingError:
    brainbox_error: str|None = None
    parse_error: str|None = None
    not_found_in_cache: bool = False



@dataclass
class BrainBoxMappingData(Generic[T]):
    mapping: 'BrainBoxMapping[T]'
    source: tuple[T,...]
    errors: tuple[BrainBoxMappingError,...]
    cache: Path | None
    tasks: tuple[IObjectConverter.Output,...]|None = None
    is_task_cached: tuple[bool,...]|None = None
    llm_answer: tuple[str|None,...]|None = None
    parsed_llm_answer: tuple[Any,...]|None = None
    result: tuple[T,...]|None = None
    _cache_manager: ICacheManager[str] = field(default_factory=ICacheManager)

    def __post_init__(self):
        if self.cache is not None:
            self._cache_manager = JsonCacheManager(self.cache)

    def build_task_and_tags(self):
        tasks = []
        is_cached = []
        for index, source in enumerate(self.source):
            task = self.mapping.object_to_task.convert(source)
            is_cached.append(self._cache_manager.contains(task.cache_key))
            task.tags['index'] = index
            tasks.append(task)
        self.tasks = tuple(tasks)
        self.is_task_cached = tuple(is_cached)


    def build_collector_task(self):
        if self.tasks is None:
            self.build_task_and_tags()
        try:
            from brainbox import BrainBox
            from brainbox.deciders import Ollama, Collector
        except ImportError as ex:
            raise "Install kaia-brainbox to use the automatical task building" from ex

        builder = Collector.TaskBuilder()
        for task, is_cached in zip(self.tasks, self.is_task_cached):
            if is_cached:
                continue
            builder.append(task.task, task.tags)
        return builder.to_collector_pack('to_array')


    def _consume_results(self, result):
        index_to_result = {}
        for item in result:
            index = item['tags']['index']
            if item['error'] is not None:
                self.errors[index].llm_error = item['error']
                index_to_result[index] = None
            else:
                index_to_result[index] = item['result']

        llm_answer = [None for _ in self.source]
        for index, task in enumerate(self.tasks):
            if index in index_to_result:
                result = index_to_result[index]
                llm_answer[index] = result
                self._cache_manager.store(task.cache_key, result)
            else:
                result = self._cache_manager.get(task.cache_key)
                if result is not None:
                    llm_answer[index] = result
                else:
                    self.errors[index].not_found_in_llm_nor_cache = True
        self.llm_answer = tuple(llm_answer)

    def _parse(self):
        parsed = []
        for index, item in enumerate(self.llm_answer):
            if item is None:
                parsed.append(None)
                continue
            if self.mapping.parser is None:
                parsed.append(item)
                continue
            try:
                value = self.mapping.parser(item)
            except:
                self.errors[index].parse_error = traceback.format_exc()
                value = None
            parsed.append(value)
        self.parsed_llm_answer = tuple(parsed)

    def _apply(self):
        application = []
        for item, parsed, task in zip(self.source, self.parsed_llm_answer, self.tasks):
            if parsed is None:
                continue
            for result in self.mapping.applicator.apply(item, parsed):
                if self.mapping.tags_address is not None:
                    self.mapping.tags_address.set(result, task.tags)
                application.append(result)
        self.result = tuple(application)


    def apply_result(self, result):
        self._consume_results(result)
        self._parse()
        self._apply()

    def execute(self, api) -> 'BrainBoxMappingData[T]':
        self.build_task_and_tags()
        task = self.build_collector_task()
        result = api.execute(task)
        self.apply_result(result)
        return self


@dataclass
class BrainBoxMapping(Generic[T]):
    object_to_task: IObjectConverter
    applicator: IApplicator
    parser: IParser|None = None
    tags_address: Address|None = None
    data: BrainBoxMappingData[T]|None = None

    def create(self, source: Iterable[T], cache: Path|None = None) -> BrainBoxMappingData[T]:
        source = tuple(source)
        errors = tuple(BrainBoxMappingError() for _ in source)
        return BrainBoxMappingData(
            self,
            source,
            errors,
            cache
        )
