from typing import Callable, Generic, TypeVar
from .chara_stack import CharaStack
from .logger_definition import logger
from .function_to_name import function_to_name
import pickle
from .result_handling import write_result, find_result, read_result, ResultType

TCharaCallReturn = TypeVar('TCharaCallReturn')


class CharaCaller(Generic[TCharaCallReturn]):
    def __init__(self,
                 stack: CharaStack,
                 function: Callable[..., TCharaCallReturn],
                 name: str|None = None,
                 result_type: ResultType = ResultType.Pickle
                 ):
        self.stack = stack
        self.function = function
        self.result_type = result_type

        if name is None:
            self.name = function_to_name(function)
        else:
            self.name = name

    def __call__(self, *args, **kwargs) -> TCharaCallReturn:
        current = self.stack.push(self.name)
        log_file = current.folder/'.log'
        result_file = find_result(current.folder)
        try:
            if result_file is not None:
                log = pickle.loads(log_file.read_bytes())
                for item in log:
                    logger.log(item)
                return read_result(result_file)

            log = []
            with logger.with_callback(log.append):
                section_name = '/'.join(f'{c.name} ({c.index})' if c.name else '' for c in self.stack.stack)
                with logger.section(section_name):
                    try:
                        result = self.function(*args, **kwargs)
                        write_result(current.folder, self.result_type, result)
                        return result
                    except Exception as e:
                        logger.error(e)
                        raise
                    finally:
                        try:
                            log_file.write_bytes(pickle.dumps(log))
                        except Exception as e:
                            logger.error("Cannot write the log")
        finally:
            self.stack.pop()
