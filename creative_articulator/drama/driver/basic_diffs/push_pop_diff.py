from ...data import IDiff, Node
from .story_state import StoryState
from .scene_state import SceneState


class IFlowBreakingDiff(IDiff):
    pass


class PopDiff(IFlowBreakingDiff):
    def apply(self, root: Node):
        state = root[StoryState]
        if state.current_node is None:
            raise ValueError("Cannot pop from the empty node")
        state.current_node[SceneState].finalized = True
        state.current_node = state.current_node.parent
        if state.current_node is None:
            state.finalized = True


class PushDiff(IFlowBreakingDiff):
    @staticmethod
    def find_non_finalized_child(node: Node) -> Node|None:
        for child in node.children:
            if child[SceneState].finalized:
                continue
            return child
        return None


    def apply(self, root: Node):
        current_node = root[StoryState].current_node
        child = PushDiff.find_non_finalized_child(current_node)
        if child is not None:
            root[StoryState].current_node = child
        else:
            raise ValueError("Push diff failed as all the children are finalized. PopDiff should be issued instead.")
