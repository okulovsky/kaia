from typing import Iterable

from .elaboration_case import ElaborationCase
from ...data import Node, IDiff
from ...scene import IElaborator, ISceneRules, SceneHint
from ..plan import IPlanFactory
from foundation_kaia.marshalling import Serializer
from chara.common.llm import ILLM
from pathlib import Path


class Elaborator(IElaborator):
    def __init__(self, source: ILLM[ElaborationCase, SceneHint]):
        self.request = (source
                        .default()
                        .template(Path(__file__).parent/'elaboration.jinja')
                        .result_type(SceneHint)
                        .to_request())

    def create_hint(self, node: Node) -> SceneHint:
        factory = node[IPlanFactory]
        plan = factory.describe(node[ISceneRules].get_actors())
        case = ElaborationCase(
            node,
            plan,
            Serializer.parse(SceneHint).to_json(plan.hint),
        )
        return self.request.execute(case)

    def elaborate(self, node: Node) -> Iterable[IDiff]:
        raise NotImplementedError()
