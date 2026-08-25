from .plan import Plan, IPlanFactory
from ...data import CharacterReference
from dataclasses import dataclass
from ...scene import SceneHint, SceneStageHint, Actors


@dataclass
class Persuasion(IPlanFactory):
    target: CharacterReference
    goal: str

    def describe(self, actors: Actors) -> Plan:
        plan = f'{actors.others(self.target)} need to convince {self.target} to agree to the following: "{self.goal}".'

        actions = [
            ["strongly refuses", "offers"],
            ["refuses, but considering options", "pushes"],
            ["unwillingly agrees", "going all in to achieve agreement"]
        ]

        stages = []
        for i in range(len(actions)):
            stage = SceneStageHint({})
            for side in actors.get_sides(self.target):
                if side.is_lead:
                    stage.character_hints[side.character.name] = [actions[i][0]+" to do "+self.goal]
                else:
                    stage.character_hints[side.character.name] = [actions[i][1]+" to do "+self.goal]
            stages.append(stage)

        return Plan(
            plan,
            SceneHint(stages)
        )









