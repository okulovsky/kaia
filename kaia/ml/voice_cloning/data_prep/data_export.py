from yo_fluq_ds import *
from kaia.brainbox import MediaLibrary
import soundfile as sf
from io import BytesIO
from pathlib import Path
from .annotation import AudioAnnotator

def _add_marks_and_selection(lib: MediaLibrary, feedback):
    reversed = {file: mark for mark, ar in feedback.items() for file in ar}
    df = lib.to_df()
    df = df.merge(pd.Series(reversed).to_frame('mark'), left_on='filename', right_index=True, how='left')
    df.mark = df.mark.fillna('no')
    df = df.merge(
        df.loc[df.mark == 'good'][['voice', 'text']].drop_duplicates().set_index(['voice', 'text']).assign(
            in_good_group=True),
        left_on=('voice', 'text'),
        right_index=True,
        how='left')
    df.in_good_group = df.in_good_group.fillna(False)

    assert (df.loc[df.mark == 'good'].groupby(['voice', 'text']).size() == 1).all()

    selected_by_ok = (
        df
        .loc[(df.mark == 'ok') & ~df.in_good_group]
        .feed(fluq.add_ordering_column(['voice', 'text'], ('option_index', False)))
        .feed(lambda z: z.loc[z.order == 0])
    ).filename

    df['selected'] = False
    df.loc[df.mark == 'good', 'selected'] = True
    df.loc[df.filename.isin(selected_by_ok), 'selected'] = True

    records_dict = lib.mapping
    for row in Query.df(df):
        rec = records_dict[row.filename]
        for key in ['selected','mark']:
            rec.tags[key] = row[key]



def _add_durations(lib: MediaLibrary):
    for record in Query.en(lib.records).feed(fluq.with_progress_bar()):
        io = BytesIO(record.get_content())
        f = sf.SoundFile(io)
        record.tags['duration'] = f.frames / f.samplerate


def _replace_texts(lib: MediaLibrary, replacements: dict):
    for record in lib.records:
        text = record.tags['text']
        for key, value in replacements.items():
            text = text.replace(key, value)
        record.tags['text'] = text


def _correct_tags(lib: MediaLibrary, file_to_origin: Dict[str, str], voice_replacements: Optional[Dict[str, str]]):
    for record in lib.records:
        if voice_replacements is not None:
            record.tags['voice'] = voice_replacements.get(record.tags['voice'], record.tags['voice'])
        record.tags['origin'] = file_to_origin.get(record.filename, '')


def finalize_annotation(
        library_to_annotation: Dict[Path, Path],
        output_path: Path,
        string_replacements: Optional[Dict[str, str]] = None,
        voice_replacements: Optional[Dict[str, str]] = None
):
    media_libraries = []
    annotations = {}
    for media_library, feedback_file in library_to_annotation.items():
        media_libraries.append(media_library)
        annotations = AudioAnnotator.load(feedback_file, annotations)

    file_to_origin = {}
    for media_library in media_libraries:
        library = MediaLibrary.read(media_library)
        for record in library.records:
            file_to_origin[record.filename] = media_library.name

    lib = MediaLibrary.read(*media_libraries)
    _correct_tags(lib, file_to_origin, voice_replacements)
    _add_marks_and_selection(lib, annotations)
    _add_durations(lib)
    if string_replacements is not None:
        _replace_texts(lib, string_replacements)
    lib.save(output_path)


def dataset_features_statistics(golden_set_location, df):
    gs = FileIO.read_json(golden_set_location)
    from copy import copy
    rows = []
    for item in gs:
        row = copy(item['stats'])
        row['text'] = item['text']
        rows.append(row)
    gdf = pd.DataFrame(rows).set_index('text')
    CS = list(gdf.columns)

    sdf = (
        df[['text', 'voice']]
        .merge(gdf, left_on='text', right_index=True)
        .drop('text', axis=1)
        .groupby('voice')[CS]
        .sum()
        .unstack()
        .to_frame('cnt')
        .reset_index()
    )
    sdf.columns = ['feature', 'voice', 'cnt']
    assert sdf.shape[0] == len(sdf.voice.unique()) * len(sdf.feature.unique())
    return sdf