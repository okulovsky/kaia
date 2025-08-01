from typing import *
from .kaia_skill import IKaiaSkill
from eaglesong.core import Automaton, ContextRequest, AutomatonExit, Listen, Return
from grammatron import Template
from avatar.services import IntentsPack, ChatCommand
from dataclasses import dataclass, field
import traceback
from datetime import datetime
from .automaton_not_found_skill import AutomatonNotFoundSkill
from .exception_in_skill import ExceptionHandledSkill
from .feedback import Feedback
from loguru import logger


@dataclass
class ActiveSkill:
    skill: IKaiaSkill
    automaton: Automaton


@dataclass
class AssistantHistoryItemReply:
    timestamp: datetime
    message: Any
    follow_up: Any

@dataclass
class AssistantHistoryItem:
    timestamp: datetime
    message: Any
    replies: List[AssistantHistoryItemReply] = field(default_factory=list)
    exception: Optional[str] = None

    @property
    def last_interation_timestamp(self):
        if len(self.replies) == 0:
            return self.timestamp
        return self.replies[-1].timestamp




class KaiaAssistant:
    def __init__(self,
                 skills: Iterable[IKaiaSkill],
                 automaton_not_found_skill: IKaiaSkill| None = None,
                 additional_intents: Optional[Iterable[Template]] = None,
                 additional_replies: Optional[Iterable[Template]] = None,
                 exception_in_skill: Optional[IKaiaSkill] = None,
                 max_history_length = 20,
                 datetime_factory: Callable[[], datetime] = datetime.now,
                 raise_exception: bool = False,
                 custom_words_in_core_intents: dict[str, str] = None,
                 default_language: str = 'en',
                 language_change_callback: Callable[[str], None] = None
                 ):
        self.skills = tuple(skills)
        self.active_skills: list[ActiveSkill] = []
        self.history: list[AssistantHistoryItem] = []
        self.max_history_length = max_history_length
        self.datetime_factory = datetime_factory
        self.raise_exceptions = raise_exception
        self.custom_words_in_core_intents = custom_words_in_core_intents
        self.default_language = default_language
        self.language_change_callback = language_change_callback

        self.all_skills = tuple(skills)

        self.automaton_not_found_skill = self._check_special_skill(
            automaton_not_found_skill,
            AutomatonNotFoundSkill(),
            'automaton_not_found_skill'
        )
        self.exception_in_skill = self._check_special_skill(
            exception_in_skill,
            ExceptionHandledSkill(),
            'exception_in_skill'
        )

        self.additional_intents = [] if additional_intents is None else list(additional_intents)
        self.additional_replies = [] if additional_replies is None else list(additional_replies)


    def _check_special_skill(self, skill, default, field):
        result = default
        if skill is not None:
            if skill.get_type() != IKaiaSkill.Type.SingleLine:
                raise ValueError(f'Only a single-line skill can be `{field}')
            result = skill
        self.all_skills+=(result,)
        return result




    def get_replies(self, include_intents = False):
        templates = []
        for skill in self.all_skills:
            templates.extend(skill.get_replies())
            if include_intents:
                for intent in skill.get_intents():
                    templates.append(intent)
        templates.extend(self.additional_replies)
        if include_intents:
            templates.extend(self.additional_intents)
        return templates


    def get_intents(self) -> list[IntentsPack]:
        core_intents = [i for skill in self.all_skills for i in skill.get_intents()] + self.additional_intents
        packs = []
        packs.append(IntentsPack(
            'CORE',
            tuple(core_intents),
            {} if self.custom_words_in_core_intents is None else self.custom_words_in_core_intents
        ))
        for skill in self.all_skills:
            packs.extend(skill.get_extended_intents_packs())
        return packs


    def _get_automaton(self, input, context) -> ActiveSkill:

        for skill in reversed(self.active_skills):
            if skill.skill.should_proceed(input):
                logger.info('Continuation: {input} continues {skill.skill.get_name()}')
                return skill

        choosen_skill = None
        for skill in self.skills:
            if not skill.should_start(input):
                continue
            choosen_skill = skill
            logger.info('Initiation: {input} initiates {skill.get_name()}')
            break

        if choosen_skill is None:
            choosen_skill = self.automaton_not_found_skill

        aut = Automaton(choosen_skill.get_runner(), context)
        active_skill = ActiveSkill(choosen_skill, aut)
        if choosen_skill.get_type() != IKaiaSkill.Type.SingleLine:
            self.active_skills.append(active_skill)

        return active_skill


    def _remove_active_skill(self, active_skill):
        self.active_skills = [a for a in self.active_skills if a != active_skill]

    def _one_step(self, input, context):
        history_item = AssistantHistoryItem(self.datetime_factory(), input)
        self.history.append(history_item)
        self.history = self.history[-self.max_history_length:]
        active_skill = self._get_automaton(input, context)
        language = active_skill.skill.get_language()
        if language is None:
            language = self.default_language
        if language is not None and self.language_change_callback is not None:
            self.language_change_callback(language)

        try:
            while True:
                reply = active_skill.automaton.process(input)
                if isinstance(reply, Listen):
                    return (reply, None)
                if isinstance(reply, AutomatonExit):
                    self._remove_active_skill(active_skill)
                    if isinstance(reply, Return) and reply.value is not None and isinstance(reply.value, Feedback):
                        return None, reply.value.content
                    return Listen(), None
                input = yield reply
                reply_history_item = AssistantHistoryItemReply(self.datetime_factory(), reply, input)
                history_item.replies.append(reply_history_item)
        except:
            if self.raise_exceptions:
                raise
            ex = traceback.format_exc()
            yield ChatCommand(ex, ChatCommand.MessageType.error)
            if self.exception_in_skill is not None:
                yield from self.exception_in_skill.get_runner()()
        return Listen(), None


    def __call__(self):
        input = yield
        while True:
            if isinstance(input, Template):
                raise ValueError("Template is found as an input for KaiaAssistant. Did you forget `utter()`?")
            context = yield ContextRequest()
            listen, returned = yield from self._one_step(input, context)
            if returned is not None:
                input = returned
            else:
                input = yield listen








