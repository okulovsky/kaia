from typing import Any

from .summarization_base import SummarizationBase, Summarization
from ....common import Node
from ...model import NodeData, TextCache
from chara.common.llm import ILLM
from pathlib import Path


class BlockSummarization(SummarizationBase):
    def __init__(self,
                 source: ILLM,
                 summary_length
                 ):
        super().__init__(
            source
            .default()
            .template(Path(__file__).parent / 'block_summarization.jinja')
            .entities(summary_length=summary_length)
            .to_request()
        )
        self.summary_length = summary_length


    def prepare(self, node: Node) -> Any:
        if node[NodeData].node_type != NodeData.Type.Block:
            return None
        text = node[TextCache].text
        if len(text) <= self.summary_length:
            return SummarizationBase.Task(ready_summary=text)
        else:
            return SummarizationBase.Task(brainbox_task=self.request.create_task(node))


class NodeSummarization(SummarizationBase):
    def __init__(self,
                 source: ILLM,
                 summary_length
                 ):
        super().__init__(
            source
            .default()
            .template(Path(__file__).parent / 'node_summarization.jinja')
            .entities(summary_length=summary_length)
            .to_request()
        )
        self.summary_length = summary_length

    def prepare(self, node: Node) -> Any:
        if node[NodeData].node_type == NodeData.Type.Block:
            return None
        text = ' '.join(n[Summarization].summary for n in node.children)
        if len(text) <= self.summary_length:
            return SummarizationBase.Task(ready_summary=text)
        return SummarizationBase.Task(brainbox_task=self.request.create_task(node))
