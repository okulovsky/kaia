import uuid
from ..basics import BlockType, NodeData, NodeType, ParagraphArray, TextCache
from ....common import Node
from .text_fragment import TextFragment
from .collate import collate, DEFAULT_MIN_MATCH
from .collate_sections import collate_sections
from .file_to_sections import file_to_sections
from .section_to_big_blocks import section_to_big_blocks
from .separate_to_known_base import separate_to_known_base
from .separate_to_small_blocks import separate


class Algorithms:
    """
    Declare here all the methods you're going to use as proxies to other methods in this folder.
    Don't call collate or collate sections directly, only with the proxy.
    This is required for configurability: if I want to change the algorithm of this or that step, I'll create a descendant of the class,
    and I won't have to rewrite all of the code
    """

    def __init__(self, max_block_length: int = 1000, min_match: float = DEFAULT_MIN_MATCH):
        self.max_block_length = max_block_length
        self.min_match = min_match

    def file_to_sections(self, paragraphs: ParagraphArray) -> list[TextFragment[NodeData]]:
        return file_to_sections(paragraphs)

    def section_to_big_blocks(self, section: ParagraphArray) -> list[TextFragment[NodeData]]:
        return section_to_big_blocks(section)

    def collate(self, incoming: tuple[TextFragment,...], base: tuple[TextFragment,...]):
        collate(incoming, base, self.min_match)

    def collate_sections(self, incoming: tuple[TextFragment[NodeData],...], base: tuple[TextFragment[NodeData],...]):
        collate_sections(incoming, base, self.min_match)

    def separate(self, text: ParagraphArray) -> list[TextFragment]:
        return separate(text, self.max_block_length)

    def separate_to_known_base(self, text: ParagraphArray, base: list[TextFragment]) -> list[TextFragment]:
        return separate_to_known_base(text, base, self.max_block_length, self.min_match)

    def node_to_fragments(self, node: Node) -> list[TextFragment[NodeData]]:
        return [TextFragment(child[TextCache].paragraphs, child[NodeData]) for child in node.children]

    def new_block_data(self, paragraphs: ParagraphArray, block_type: int) -> NodeData:
        return NodeData(NodeType.Block, uuid.uuid4().hex, None, paragraphs.simhash, block_type)

    def final_file_to_sections(self, paragraphs: ParagraphArray, base: Node) -> list[TextFragment[NodeData]]:
        """
        Should separate file to sections,
        get the base split to sections from the base,
        and collate them
        For those that have match, old ID should be assigned in the NodeData
        For those that haven't, new ID should be created
        """
        incoming = self.file_to_sections(paragraphs)
        self.collate(tuple(incoming), tuple(self.node_to_fragments(base)))
        for fragment in incoming:
            if fragment.match is not None:
                fragment.payload.id = fragment.match.matched_with.payload.id
        return incoming



    def final_section_to_blocks(self, incoming: ParagraphArray, base: Node) -> list[TextFragment[NodeData]]:
        """
        Should separate section to big blocks
        Collate these big blocks with the old ones with .collate_sections
        Then, the blocks that are plans and separator, they should collate with no more than one of the old blocks, so assign ID to the NodeData accordingly

        Then, text blocks. If they do not have match, separate them with separate_to_small_blocks and that's it, just assign new ids
        If they do have match, separate the new block with the known base, and then, again, take old id where there is a match, and new id where there is no match
        """
        big_blocks = self.section_to_big_blocks(incoming)
        self.collate_sections(tuple(big_blocks), tuple(self.node_to_fragments(base)))

        result: list[TextFragment[NodeData]] = []
        for block in big_blocks:
            if block.payload.block_type != BlockType.Text:
                if block.match is not None:
                    matched = block.match.matched_with.payload
                    if len(matched) == 1:
                        block.payload.id = matched[0].payload.id
                result.append(block)
                continue

            if block.match is None:
                pieces = self.separate(block.paragraphs)
                for piece in pieces:
                    piece.payload = self.new_block_data(piece.paragraphs, BlockType.Text)
            else:
                pieces = self.separate_to_known_base(block.paragraphs, block.match.matched_with.payload)
                for piece in pieces:
                    piece.payload = self.new_block_data(piece.paragraphs, BlockType.Text)
                    if piece.match is not None:
                        piece.payload.id = piece.match.matched_with.payload.id
            result.extend(pieces)
        return result
