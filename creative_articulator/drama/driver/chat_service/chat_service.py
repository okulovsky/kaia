import threading
from contextlib import contextmanager
from avatar.daemon import message_handler, ChatCommand, InitializationEvent, TextEvent, IMessage
from ...data import DiffList, Node, Message, IDiff
from pathlib import Path
from ..engines import StoryDriver
from .node_helper import NodeHelper, MessageBranch
from ..basic_diffs import AddMessageDiff
from .tree_status import TreeStatus
from .messages import *


class ChatService:
    def __init__(self,
                 driver: StoryDriver,
                 path_to_save_file: Path|None = None,
                 protagonist_name: str = 'User'
                 ):
        self.driver = driver
        self.node_controller = NodeHelper(path_to_save_file)
        self.protagonist_name = protagonist_name
        self._answering_chat_message_id: str|None = None
        self._lock = threading.Lock()
        self._requested_delayed_tasks_reference_ids: set[str] = set()

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_lock']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = threading.Lock()

    def _to_chat_command(self, node: Node) -> ChatCommand:
        message = node[Message]
        details = None
        if node.parent is not None:
            idx = node.parent.children.index(node)
            details = f"{idx+1}/{len(node.parent.children)}"
        diff_list = node[DiffList]
        hover_string = '\n'.join(type(d).__name__ for d in diff_list) if diff_list else None
        if diff_list:
            details = f"({len(diff_list)}) {details}" if details else f"({len(diff_list)})"
        return ChatCommand(
            message.__str__(),
            ChatCommand.MessageType.from_user if message.from_user else ChatCommand.MessageType.to_user,
            message.speaker,
            message_id=message.id,
            details=details,
            hover_string=hover_string,
        )

    def _process_diff(self, diff: IDiff, base_event: IMessage):
        diff.apply(self.driver.story)
        if isinstance(diff, AddMessageDiff):
            self.node_controller.append_message(diff.message)
        self.node_controller.current[DiffList].append(diff)
        self.node_controller.save()
        if self.node_controller.current.has(Message):
            yield self._to_chat_command(self.node_controller.current).as_reply_to(base_event)

    def _generate(self, base_event: IMessage):
        for diff in self.driver.generate():
            with self._lock:
                if base_event.envelop.id != self._answering_chat_message_id:
                    return True
                yield from self._process_diff(diff, base_event)
                if base_event.envelop.id != self._answering_chat_message_id:
                    return True
        return False


    @contextmanager
    def _critical(self, event):
        # Not interrupted: holds the lock for the whole block, so no other
        # handler's critical section (and thus no other _answering_chat_message_id
        # change) can happen while this one runs.
        with self._lock:
            self._answering_chat_message_id = event.envelop.id
            yield

    @message_handler
    def on_initialize(self, event: InitializationEvent):
        with self._critical(event):
            if self.node_controller.path_to_log_file is None:
                self.driver.reset()
            else:
                self.node_controller.load()
                for n in self.node_controller.current.ancestors(True):
                    if not n[TreeStatus].is_root and n.has(Message):
                        yield self._to_chat_command(n)
                self.driver.reset(self._diffs_for(self.node_controller.current))
        interrupted = yield from self._generate(event)
        yield ChatConfirmation(interrupted).as_confirmation_for(event)


    @message_handler
    def on_text_event(self, event: TextEvent):
        with self._critical(event):
            if event.text.strip():
                message = Message.from_text(event.text, self.protagonist_name, True)
                yield from self._process_diff(AddMessageDiff(message), event)

        interrupted = yield from self._generate(event)
        yield ChatConfirmation(interrupted).as_confirmation_for(event)

    def _build_hide_event(self, branch: MessageBranch) -> DeleteChatMessagesCommand:
        return DeleteChatMessagesCommand([m[Message].id for m in branch.descendants+[branch.target]])

    def _diffs_for(self, node: Node) -> list[IDiff]:
        diffs = []
        for n in node.ancestors(True):
            if not n[TreeStatus].is_root:
                diffs.extend(n[DiffList])
        return diffs

    def _on_branch_switch(self, parent: Node, index: int, hidden_branch: MessageBranch):
        if index < 0:
            index = len(parent.children) - 1
        diffs = []
        for n in parent.ancestors(True):
            if not n[TreeStatus].is_root:
                diffs.extend(n[DiffList])
        if index >= len(parent.children):  # That means, the non-existing "next" was requested => generate new
            self.node_controller.current = parent
            self.driver.reset(diffs)
            return True


        self.node_controller.select(parent.children[index])
        end_node = parent
        while True:
            new_end_node = self.node_controller.get_selected_child(end_node)
            if new_end_node is None:
                break
            end_node = new_end_node
            diffs.extend(end_node[DiffList])
            yield self._to_chat_command(end_node)
        self.node_controller.current = end_node
        self.node_controller.save()
        self.driver.reset(diffs)
        return False


    @message_handler
    def on_change_request(self, event: SwipeChatMessageEvent):
        with self._critical(event):
            branch = self.node_controller.find_message_in_current_branch(event.message_id)
            index = branch.parent.children.index(branch.target)
            index = index + (-1 if event.swipe_to_left else +1)
            should_generate = False
            # index < 0 with a single child would otherwise wrap around to
            # that same child in _on_branch_switch, hiding and immediately
            # re-showing the branch we're already on -- a no-op swipe.
            if not (index < 0 and len(branch.parent.children) == 1):
                yield self._build_hide_event(branch)
                should_generate = yield from self._on_branch_switch(branch.parent, index, branch)

        interrupted = False
        if should_generate:
            interrupted = yield from self._generate(event)
        yield ChatConfirmation(interrupted).as_confirmation_for(event)

    def _remove_floor(self, parent: Node):
        children = parent.children
        for child in children:
            parent.remove(child)

    @message_handler
    def on_delete_request(self, event: DeleteChatMessageEvent):
        with self._critical(event):
            branch = self.node_controller.find_message_in_current_branch(event.message_id)
            yield self._build_hide_event(branch)
            self._remove_floor(branch.parent)
            should_generate = yield from self._on_branch_switch(branch.parent, 0, branch)

        interrupted = False
        if should_generate:
            interrupted = yield from self._generate(event)

        yield ChatConfirmation(interrupted).as_confirmation_for(event)
