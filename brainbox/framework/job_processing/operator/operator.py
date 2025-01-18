from ..core import OperatorMessage, OperatorState
import traceback
from datetime import datetime
from .decider_log import DeciderLogger
from ...common import IDecider, DeciderContext, File, Locator
from .file_postprocessor import file_postprocess
import time


class DeciderOperator:
    def __init__(self, state: OperatorState):
        self.state = state
        self.current_id: str|None = None

    def cycle(self):
        self.state.logger.decider(self.state.key).event("Starting processing cycle")
        while True:
            if self.state.exit_request:
                break
            success = self.next_task()
            if not success:
                time.sleep(0.01)
        self.state.logger.decider(self.state.key).event("Exiting processing cycle")


    def next_task(self):
        if self.state.jobs_queue.empty():
            if self.state.busy:
                self.state.busy = False
                self.state.not_busy_since = datetime.now()
                self.state.logger.decider(self.state.key).event('Not busy')
            return False

        if not self.state.busy:
            self.state.busy = True
            self.state.logger.decider(self.state.key).event('Busy')

        job = self.state.jobs_queue.get()
        self.current_id = job.id
        self.state.logger.decider(self.state.key).event(f'Processing task {self.current_id}')
        self.state.results_queue.put(OperatorMessage(self.current_id, OperatorMessage.Type.accepted))
        self.state.logger.task(self.current_id).event('Accepted')

        method = job.method
        arguments = job.arguments


        try:
            decider = self.state.api
            decider.context._current_job_id = self.current_id
            decider.context._logger = DeciderLogger(self.current_id, self.state.results_queue)

            if method is not None:
                method_instance = getattr(decider, method)
            elif callable(decider):
                method_instance = decider
            else:
                raise ValueError(f'Method is not set for {self.state.key.decider_name}, and the decider is not callable')

            result = method_instance(**arguments)

            result = file_postprocess(result, decider.cache_folder)

            self.state.results_queue.put(OperatorMessage(self.current_id, OperatorMessage.Type.result, result))
            self.state.logger.task(self.current_id).event('Finished with a success')
            return True
        except:
            msg = f"Error when executing job {self.current_id} for decider {self.state.key}\n" + traceback.format_exc()
            self.state.results_queue.put(OperatorMessage(self.current_id, OperatorMessage.Type.error, msg))
            self.state.logger.task(self.current_id).event('Finished with a failure')
            return False
        finally:
            self.current_id = None
