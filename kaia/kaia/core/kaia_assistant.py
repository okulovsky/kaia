from typing import *
from .kaia_skill import IKaiaSkill
from ...eaglesong.core import Automaton, ContextRequest, AutomatonExit, Listen
from kaia.dub.core import Template
from ..gui import KaiaMessage
from dataclasses import dataclass, field
import traceback
from datetime import datetime

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
                 automaton_not_found_skill: IKaiaSkill,
                 additional_intents: Optional[Iterable[Template]] = None,
                 additional_replies: Optional[Iterable[Template]] = None,
                 exception_in_skill: Optional[IKaiaSkill] = None,
                 max_history_length = 20,
                 datetime_factory: Callable[[], datetime] = datetime.now,
                 raise_exception: bool = True
                 ):
        self.skills = tuple(skills)
        self.active_skill: Optional[ActiveSkill] = None
        self.history: list[AssistantHistoryItem] = []
        self.max_history_length = max_history_length
        self.datetime_factory = datetime_factory
        self.raise_exceptions = raise_exception

        all_skills = list(skills)

        self.automaton_not_found_skill = automaton_not_found_skill
        if self.automaton_not_found_skill.get_type() != IKaiaSkill.Type.SingleLine:
            raise ValueError('Only a single-line skill can be `automaton_not_found_skill')
        all_skills.append(self.automaton_not_found_skill)

        self.exception_in_skill = exception_in_skill
        if self.exception_in_skill is not None:
            if self.exception_in_skill.get_type() != IKaiaSkill.Type.SingleLine:
                raise ValueError('Only a single-line skill can be `exception_in_skill')
            all_skills.append(self.exception_in_skill)

        self.all_skills = tuple(all_skills)
        self.additional_intents = [] if additional_intents is None else list(additional_intents)
        self.additional_replies = [] if additional_replies is None else list(additional_replies)



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


    def get_intents(self):
        return [i for skill in self.all_skills for i in skill.get_intents()] + self.additional_intents


    def _get_automaton(self, input, context) -> Tuple[Optional[Automaton], bool]:
        if self.active_skill is not None:
            if self.active_skill.skill.should_proceed(input):
                return self.active_skill.automaton, True

        for skill in self.skills:
            if not skill.should_start(input):
                continue
            aut = Automaton(skill.get_runner(), context)
            if skill.get_type() != IKaiaSkill.Type.SingleLine:
                self.active_skill = ActiveSkill(skill, aut)
                return aut, True
            return aut, False

        aut = Automaton(self.automaton_not_found_skill.get_runner(), context)
        return aut, False

    def _one_step(self, input, context):
        history_item = AssistantHistoryItem(self.datetime_factory(), input)
        self.history.append(history_item)
        self.history = self.history[-self.max_history_length:]

        aut, is_active_skill = self._get_automaton(input, context)

        try:
            while True:
                reply = aut.process(input)
                if isinstance(reply, Listen):
                    return reply
                if isinstance(reply, AutomatonExit):
                    if is_active_skill:
                        self.active_skill = None
                    break
                input = yield reply
                reply_history_item = AssistantHistoryItemReply(self.datetime_factory(), reply, input)
                history_item.replies.append(reply_history_item)
            return Listen()
        except:
            if self.raise_exceptions:
                raise
            ex = traceback.format_exc()
            yield KaiaMessage(True, ex, True)
            if self.exception_in_skill is not None:
                yield from self.exception_in_skill.get_runner()()


    def __call__(self):
        while True:
            input = yield
            context = yield ContextRequest()
            if isinstance(input, Template):
                raise ValueError("Template is found as an input for KaiaAssistant. Did you forget `utter()`?")
            listen = yield from self._one_step(input, context)
            yield listen








