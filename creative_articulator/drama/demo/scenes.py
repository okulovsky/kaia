from dataclasses import dataclass

from chara.common.llm import Question, QuestionList

from ..data import Character, CharacterReference
from ..scene import Actors, SceneHint, SceneStageHint
from ..scene.scene_engine import SceneRules
from .characters import CHARACTERS, MATROSKIN, PECHKIN, SHARIK


@dataclass
class Stage:
    hints: dict[str, list[str]]
    announcement: str | None = None


@dataclass
class DemoScene:
    title: str
    opening: str
    ending_field: str
    ending_question: str
    stages: tuple[Stage, ...] = ()

    def build_actors(self, protagonist: Character) -> Actors:
        return Actors(
            CharacterReference(protagonist),
            CharacterReference([c for c in CHARACTERS if c.name != protagonist.name]),
            self.opening,
        )

    def build_rules(self, protagonist: Character) -> SceneRules:
        stages = [
            SceneStageHint(
                {name: list(hints) for name, hints in stage.hints.items()},
                stage.announcement,
            )
            for stage in self.stages
        ]
        questions = QuestionList([Question(self.ending_field, self.ending_question, bool)])
        return SceneRules(self.build_actors(protagonist), SceneHint(stages), questions)


THE_QUARREL = DemoScene(
    title='The Quarrel',
    opening=(
        'Pechkin comes in stamping the snow off his feet. Matroskin is at the table with his accounts, '
        'Sharik is by the stove, and the two of them are sitting as far apart as the room allows, '
        'neither looking at the other.'
    ),
    ending_field='reason_told',
    ending_question=(
        'Has it been said out loud, in plain words, that Sharik came back with sneakers instead of the winter '
        'boots he was sent for, so that Pechkin now knows what the quarrel is actually about?'
    ),
    stages=(
        Stage({
            PECHKIN.name: [
                'wants to know what has happened in this house, and will not leave until he is told',
                'takes the silence between the other two as an insult to himself and a fine piece of news at once',
            ],
            MATROSKIN.name: [
                'does not answer the question at all, and makes a cutting remark about Sharik instead',
                'speaks about Sharik in the third person, as though he were not sitting in the same room',
                'does not name what the quarrel was about, no matter how the question is put',
            ],
            SHARIK.name: [
                'does not answer the question either, and returns every remark of Matroskin with one of his own',
                'insists he has done nothing wrong, without ever saying what he is accused of',
                'does not name what the quarrel was about, no matter how the question is put',
            ],
        }),
        Stage(
            {
                PECHKIN.name: [
                    'presses harder, guesses out loud, and tries to play the two of them off against each other',
                    'pretends to be leaving, in the hope that somebody will stop him with the answer',
                ],
                MATROSKIN.name: [
                    'lets slip that money was spent, and that the spending was idiotic, but still will not say on what',
                    'grumbles about who in this house earns and who in this house buys',
                ],
                SHARIK.name: [
                    'defends the purchase without naming it, and says it was his own money and his own business',
                    'hints that it is a matter of fashion, and that Matroskin understands nothing about fashion',
                ],
            },
            announcement='The wind throws a handful of snow against the window, and nobody gets up to close the shutter.',
        ),
        Stage(
            {
                PECHKIN.name: [
                    'senses he is one question away from the whole story, and asks it',
                ],
                MATROSKIN.name: [
                    'finally says it outright: Sharik was sent for winter boots and came back with sneakers',
                    'makes it clear this is what he has been sitting with all day',
                ],
                SHARIK.name: [
                    'admits he bought sneakers instead of boots, and defends them as the better thing anyway',
                ],
            },
            announcement='The frost cracks in the wall, loud as a shot, and for a moment nobody says anything.',
        ),
    ),
)


THE_TELEGRAM = DemoScene(
    title='The Telegram',
    opening=(
        'The same evening. Pechkin knows the whole story now, and he has thought of something. Matroskin and '
        'Sharik are still not speaking to each other, and the sneakers are standing by the door where everybody '
        'can see them.'
    ),
    ending_field='letter_sent',
    ending_question=(
        'Has one of them actually agreed to send the other a written message through the post office, with the '
        'wording or the price settled, rather than only talking about the idea?'
    ),
    stages=(
        Stage({
            PECHKIN.name: [
                'proposes that since the two of them will not speak, they should write to each other, '
                'and the post office is standing right here',
                'presents this as an official service of the post office, not as a favour',
            ],
            MATROSKIN.name: [
                'refuses on the grounds of cost, and asks what the post office charges per word',
                'points out that he is not going to pay money to talk to somebody sitting two metres away',
            ],
            SHARIK.name: [
                'refuses on the grounds that he has nothing whatever to say to Matroskin',
                'is entirely cheerful about refusing, and keeps changing the subject to something outdoors',
            ],
        }),
        Stage(
            {
                PECHKIN.name: [
                    'works on them one at a time, and tells each what the other would make of a refusal',
                    'quotes the tariff as though it were a bargain, and mentions that a written word is a document',
                ],
                MATROSKIN.name: [
                    'starts calculating whether a short message would come cheaper than another week of this',
                    'haggles over the price and over the number of words',
                ],
                SHARIK.name: [
                    'turns out to have something he does want said, and still will not say it out loud',
                    'worries whether writing first counts as giving in first',
                ],
            },
            announcement='Pechkin unbuttons his bag and lays a blank telegram form on the table, face up.',
        ),
        Stage(
            {
                PECHKIN.name: [
                    'pushes for the message to be dictated here and now, and has the pencil ready',
                ],
                MATROSKIN.name: [
                    'names the shortest message he is prepared to pay for, and counts the words as he says them',
                ],
                SHARIK.name: [
                    'dictates something short and unexpectedly generous, or refuses once and for all',
                ],
            },
            announcement='The lamp gutters, and the blank form is still lying in the middle of the table.',
        ),
    ),
)


SCENES = (THE_QUARREL, THE_TELEGRAM)
