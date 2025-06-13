from typing import *
from .kaia_skill import IKaiaSkill
from eaglesong.core import Automaton, ContextRequest, AutomatonExit, Listen, Return
from eaglesong.templates import Template, IntentsPack
from ..server import Message
from dataclasses import dataclass, field
import traceback
from datetime import datetime
from .automaton_not_found_skill import AutomatonNotFoundSkill
from .exception_in_skill import ExceptionHandledSkill
from .feedback import Feedback

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
                 custom_words_in_core_intents: dict[str, str] = None
                 ):
        self.skills = tuple(skills)
        self.active_skills: list[ActiveSkill] = []
        self.history: list[AssistantHistoryItem] = []
        self.max_history_length = max_history_length
        self.datetime_factory = datetime_factory
        self.raise_exceptions = raise_exception
        self.custom_words_in_core_intents = custom_words_in_core_intents

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


    def _get_automaton(self, input, context) -> Optional[Automaton]:
        for skill in reversed(self.active_skills):
            if skill.skill.should_proceed(input):
                return skill.automaton

        for skill in self.skills:
            if not skill.should_start(input):
                continue
            aut = Automaton(skill.get_runner(), context)
            if skill.get_type() != IKaiaSkill.Type.SingleLine:
                self.active_skills.append(ActiveSkill(skill, aut))
            return aut

        aut = Automaton(self.automaton_not_found_skill.get_runner(), context)
        return aut

    def _remove_automaton(self, aut: Automaton):
        self.active_skills = [a for a in self.active_skills if a.automaton != aut]

    def _one_step(self, input, context):
        history_item = AssistantHistoryItem(self.datetime_factory(), input)
        self.history.append(history_item)
        self.history = self.history[-self.max_history_length:]
        aut = self._get_automaton(input, context)

        try:
            while True:
                reply = aut.process(input)
                if isinstance(reply, Listen):
                    return (reply, None)
                if isinstance(reply, AutomatonExit):
                    self._remove_automaton(aut)
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
            yield Message(Message.Type.Error, ex)
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








