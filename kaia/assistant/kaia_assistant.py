from typing import *
from .kaia_skill import IKaiaSkill
from eaglesong.core import Automaton, ContextRequest, AutomatonExit, Listen, Return
from grammatron import Template
from avatar.daemon import IntentsPack, ChatCommand, NarrationService, State, BackendIdleReport
from dataclasses import dataclass, field
import traceback
from datetime import datetime
from .automaton_not_found_skill import AutomatonNotFoundSkill
from .exception_in_skill import ExceptionHandledSkill
from .feedback import Feedback
from loguru import logger
from .context import KaiaContext
from .common_intents import CommonIntents

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
    RHASSPY_MAIN_MODEL_NAME = 'CORE'

    def __init__(self,
                 skills: Iterable[IKaiaSkill],
                 automaton_not_found_skill: IKaiaSkill| None = None,
                 exception_in_skill: Optional[IKaiaSkill] = None,
                 datetime_factory: Callable[[], datetime] = datetime.now,
                 raise_exception: bool = False,
                 custom_words_in_core_intents: dict[str, str] = None,
                 default_language: str = 'en',
                 ):
        self.skills = tuple(skills)
        self.active_skills: list[ActiveSkill] = []
        self.datetime_factory = datetime_factory
        self.raise_exceptions = raise_exception
        self.custom_words_in_core_intents = custom_words_in_core_intents
        self.default_language = default_language
        self.current_language = default_language
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

        self.additional_intents = [CommonIntents.stop]
        self.additional_replies = []

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
            KaiaAssistant.RHASSPY_MAIN_MODEL_NAME,
            tuple(core_intents),
            {} if self.custom_words_in_core_intents is None else self.custom_words_in_core_intents
        ))
        for skill in self.all_skills:
            packs.extend(skill.get_extended_intents_packs())
        return packs


    def _get_automaton(self, input, context) -> ActiveSkill:
        for skill in reversed(self.active_skills):
            if skill.skill.should_proceed(input):
                logger.info(f'Continuation: `{input}` continues `{skill.skill.get_name()}`')
                return skill

        choosen_skill = None
        for skill in self.skills:
            if not skill.should_start(input):
                continue
            choosen_skill = skill
            logger.info(f'Initiation: `{input}` initiates `{skill.get_name()}`')
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


    def _fix_language(self, active_skill, context: KaiaContext):
        language = active_skill.skill.get_language()
        if language.type == IKaiaSkill.Language.Type.self_managed:
            return
        target_language = None
        if language.type == IKaiaSkill.Language.Type.default:
            target_language = self.default_language
        elif language.type == IKaiaSkill.Language.Type.specific:
            target_language = language.language
        if target_language is not None:
            if self.current_language is None or self.current_language != target_language:
                if context is not None:
                    state = context.get_client().run_synchronously(NarrationService.LanguageRequest(target_language), State)
                    self.current_language = state.language
                else:
                    self.current_language = target_language


    def _one_step(self, input, context:KaiaContext):
        history_item = AssistantHistoryItem(self.datetime_factory(), input)
        active_skill = self._get_automaton(input, context)

        self._fix_language(active_skill, context)

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
                yield BackendIdleReport(len(self.active_skills) == 0)
                input = yield listen








