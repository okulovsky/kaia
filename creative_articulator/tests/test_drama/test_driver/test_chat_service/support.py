from contextlib import contextmanager

from avatar.app import AvatarApi
from avatar.daemon import InitializationEvent
from avatar.messaging import AvatarDaemon, IMessage, BindingSettings
from foundation_kaia.misc import Loc

from creative_articulator.drama.data import Node, Message
from creative_articulator.drama.driver import ChatService, StoryDriver, MockEngine, IEngine


def _build_driver(time_to_message_in_seconds: float) -> StoryDriver:
    story = Node()
    story.attach(
        MockEngine(buffer_message=0, time_to_message_in_seconds=time_to_message_in_seconds, character_name="Character"),
        custom_type=IEngine,
    )
    return StoryDriver(story)


@contextmanager
def running_chat_service(tc, time_to_message_in_seconds: float = 0):
    """
    Runs a real AvatarServer in a subprocess with a ChatService bound to a
    daemon (also real: rules dispatch through its actual queue/thread model),
    and yields a client for pushing events and reading back the resulting
    ChatCommand / DeleteChatMessagesCommand messages -- i.e. tests only ever
    see inputs and outputs, never ChatService's/NodeHelper's internals.
    """
    with Loc.create_test_folder() as folder:
        with AvatarApi.test(folder) as api:
            client = api.create_client()
            client.test_case = tc
            daemon = AvatarDaemon(client.clone_client(), timeout_in_pull_in_seconds=0)
            daemon.rules.bind(ChatService(_build_driver(time_to_message_in_seconds)), BindingSettings().asynchronous())
            daemon.run_in_thread()

            # With MockEngine attached directly to the root node (no scene wrapper
            # to pause after the opening line), initialization immediately produces
            # both the opening message and MockEngine's automatic reply to it.
            replies = push_and_collect_replies(client, InitializationEvent())
            tc.assertEqual(2, len(replies))
            tc.assertEqual(str(Message.from_text("* Opening *")), replies[0].text)
            yield client


def collect_results(client, *events: IMessage, timeout: float = 5) -> list[list[IMessage]]:
    """
    Assumes every event in `events` has already been pushed. Reads messages
    until a confirmation has arrived for each of them, and returns one list
    of messages per event (in arrival order), including that event's own
    confirmation as the last entry.
    """
    results = [[] for _ in events]
    done = [False] * len(events)
    for message in client.query(timeout):
        for i, event in enumerate(events):
            if message.is_confirmation_of(event):
                results[i].append(message)
                done[i] = True
                break
            if message.envelop.reply_to == event.envelop.id:
                results[i].append(message)
                break
        if all(done):
            break
    return results


def push_and_collect_replies(client, event: IMessage, timeout: float = 5) -> list[IMessage]:
    """
    Pushes `event`, then reads messages until the confirmation for that event
    arrives, and returns every message read along the way that is a reply to
    it (the confirmation sentinel itself is not included).
    """
    client.push(event)
    results = collect_results(client, event, timeout=timeout)[0]
    return results[:-1]
