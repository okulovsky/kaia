from yo_fluq_ds import *
from kaia.brainbox import BrainBoxTask, BrainBoxTaskPack, MediaLibrary
from kaia.brainbox.deciders import Collector
from ipywidgets import VBox, HBox, Audio, Label
from copy import copy

def _to_selected(lib):
    result = {}
    for record in lib.records:
        if not record.tags['selected']:
            continue
        if record.tags['voice'] not in result:
            result[record.tags['voice']] = set()
        result[record.tags['voice']].add(record.tags['text'])
    return result


def generate_tasks(
        sentences: Iterable[str],
        voices: Iterable[str],
        lib: Optional[MediaLibrary] = None,
        task_factory: Optional[Callable[[str, str], BrainBoxTask]] = None,
        additional_tags: Optional[Dict] = None
    ):

    ids = []
    tags = {}
    tasks = []
    voices = list(voices)

    additional_tags = additional_tags if additional_tags is not None else {}

    task_factory = task_factory if task_factory is not None else (
        lambda voice, text: BrainBoxTask(
                id=BrainBoxTask.safe_id(),
                decider='TortoiseTTS',
                arguments=dict(voice=voice, text=sentence)
            )
    )

    if lib is not None:
        exclude = _to_selected(lib)
    else:
        exclude = {}

    for voice in voices:
        for sentence in sentences:
            if voice in exclude and sentence in exclude[voice]:
                continue
            task = task_factory(voice, sentence)
            tags[task.id] = dict(voice=voice, text=sentence, **additional_tags)
            ids.append(task.id)
            tasks.append(task)

    collection = BrainBoxTask(
        decider=Collector.to_media_library,
        arguments=dict(tags=tags),
        dependencies={i: i for i in ids}
    )

    return BrainBoxTaskPack(
        collection,
        tuple(tasks)
    )


def preview_media_library(ml: MediaLibrary):
    data = {}
    for record in ml.records:
        voice = record.tags['voice']
        if voice not in data:
            data[voice] = {}
        text = record.tags['text']
        if text not in data[voice]:
            data[voice][text] = []
        data[voice][text].append(record.filename)

    dct = ml.mapping

    buffer = []
    for voice in data:
        buffer.append(Label(voice.upper()))
        for text in data[voice]:
            buffer.append(Label(text))
            audios = [Audio(value=dct[file].get_content(), autoplay=False) for file in data[voice][text]]
            buffer.append(HBox(audios))

    return VBox(buffer)