from .externals.kittenbot.src.kittenbot.message_handler import KittenMessageHandler
from .externals.kittenbot.src.kittenbot.random_generator import RandomGenerator
from .externals.kittenbot.src.kittenbot.resources import ProdResources
from .externals.kittenbot.src.kittenbot.language_processing import Nlp, MorphAnalyzer
from .externals.kittenbot.src.kittenbot.actions import Reply, DocumentReplyContent, TextReplyContent
from zoo.group_chatbot.instant_reaction_skill import *

from pathlib import Path

class KittenbotSkill(TelegramInstantReactionSkill):
    def __init__(self,
                 bot_id,
                 probability,
                 agree_probability,
                 test_group_ids,
                 bot_names,
                 noun_template,
                 noun_weight,
                 verb_template,
                 verb_weight
                 ):
        path = Path(__file__).parent/'pidorbot/resources'
        rand_gen = RandomGenerator()
        resources = ProdResources(rand_gen, path)
        handler = KittenMessageHandler(
            rand_gen,
            resources,
            Nlp(MorphAnalyzer()),
            bot_id,
            probability,
            agree_probability,
            test_group_ids,
            bot_names,
            noun_template,
            noun_weight,
            verb_template,
            verb_weight
        )
        self.handler = handler

    def execute(self, update: tg.Update):
        result = self.handler.handle(update, None)

        if result is None:
            return []

        if isinstance(result, Reply):
            if isinstance(result.content, DocumentReplyContent):
                return [
                    TgCommand.mock().send_document(
                        result.reply_to.chat_id,
                        document=result.content.document,
                        filename = result.content.filename,
                        reply_to_message_id = result.reply_to.message_id
                    )
                ]
            if isinstance(result.content, TextReplyContent):
                return [
                    TgCommand.mock().send_message(
                        result.reply_to.chat_id,
                        result.content.text,
                        reply_to_message_id=result.reply_to.message_id)
                    ]
        return []

