from .common_imports import *
from datetime import datetime, timedelta

class MessageFrequencyRestricter:
    def __init__(self,
                 ids_affected: List[int],
                 delay_in_minutes: int,
                 current_time_factory: Callable[[], datetime] = datetime.now
                 ):
        self.ids_affected = ids_affected
        self.delay_in_minutes = delay_in_minutes
        self.current_time_factory = current_time_factory

    def __call__(self):
        update = yield None

        if update.effective_user.id not in self.ids_affected:
            return

        logging.info('delay_in_minutes not None. Sending restriction')
        yield TgCommand.mock().restrict_chat_member(
            chat_id = update.effective_chat.id,
            user_id = update.effective_user.id,
            until_date=self.current_time_factory() + timedelta(minutes=self.delay_in_minutes),
            permissions=tg.ChatPermissions.no_permissions()
        )
