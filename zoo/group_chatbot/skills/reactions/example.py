import logging
from kaia.infra import Loc
from telegram import Update
from telegram.ext import Application
import os

from zoo.group_chatbot.skills.reactions.reaction_handler import ReactionHandler, TriggerCondition





logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> None:
    application = Application.builder().token(os.environ['KAIA_TEST_BOT']).build()
    trigger_conditions = [
        TriggerCondition('👍', 10),
        TriggerCondition('💩', 5, 'Начальник! Этот пидарас обосрался!', should_ban=True),
        TriggerCondition('🤡',10, 'У нас тут клоун')
    ]
    ReactionHandler(application, trigger_conditions, ban_duration_hours=1, keep_records_days=1)
    application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == "__main__":
    main()



