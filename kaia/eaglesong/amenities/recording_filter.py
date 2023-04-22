import json
import logging
from kaia.eaglesong.core.subroutines import RoutineBase, Routine
import jsonpickle
import logging
from functools import partial

class RecordingFilter(Routine):
    def __init__(self, routine: Routine, level: str):
        self.routine = routine
        self.logger = logging.getLogger('eaglesong.recorder.'+level)

    @staticmethod
    def with_name(level: str):
        return partial(RecordingFilter, level=level)

    def try_jsonpickle(self, obj):
        try:
            return jsonpickle.dumps(obj)
        except:
            return json.dumps(dict(error="Not pickable"))

    def run(self, context):
        for result in Routine.ensure(self.routine).instantiate(context):
            self.logger.info('REPLY:    '+self.try_jsonpickle(result))
            yield result
            self.logger.info('FEEDBACK: '+self.try_jsonpickle(context.get_input_summary()))

    def _push_notification(self, source, context):
        self.logger.info('INCOMING at '+source+": "+self.try_jsonpickle(context.get_input_summary()))

