"""
This example removes magic from Telegram bot, explicitly creating
all the filters around Echobot routine: `PushdownFilter` and `TelegramTranslationFilter`.

Also, it adds `RecordingFilter` that logs all the messages, coming through the filter.
If you run this chatbot, you will see these messages in console and will
probably better understand their routs. However, this is not the recommended way of debugging:
the unit tests are. `RecordingFilter` can be a method of last resort in debugging
various issues _outside_ of the chatflow, but not _within_.
"""

from demos.eaglesong.common import *
from demos.eaglesong.example_01_echobot import main
from kaia.eaglesong.amenities.recording_filter import RecordingFilter

def get_skill():
    return Routine.interpretable(
        main,
        RecordingFilter.with_name('algorithm'),
        PushdownFilter,
        RecordingFilter.with_name('pushdown'),
        TelegramTranslationFilter,
        RecordingFilter.with_name('telegram')
    )


bot = Bot("recorder", factory=get_skill, add_telegram_filter=False)


if __name__ == '__main__':
    run(bot)