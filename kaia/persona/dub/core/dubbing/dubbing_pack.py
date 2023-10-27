import os
from typing import *
import zipfile
import pandas as pd
from .dto import DubbingFragment
from .dubber import Dubber
from yo_fluq_ds import *
from pathlib import Path
from kaia.brainbox.deciders.tortoise_tts.dub_collector import _save_dubbing_pack
from ...core import Dub, Template
from .fragmenter import Fragmenter

import shutil

class DubbingPack:
    def __init__(self,
                 fragments: Iterable[DubbingFragment],
                 host_folder: Optional[Path] = None,
                 errors: Optional[List[str]] = None
                 ):
        self.fragments = tuple(fragments)
        if not isinstance(self.fragments[0], DubbingFragment):
            raise ValueError('Not a dub task')
        self.df = pd.DataFrame([t.__dict__ for t in self.fragments])
        self.host_folder = host_folder
        self.errors = errors
        self.voices = tuple(set(t.voice for t in fragments))

    def create_dubber(self, voice: Optional[str] = None, option_index: int = 0):
        if voice is None:
            voice = self.voices[0]
        df = self.df.loc[(self.df.voice == voice) & (self.df.option_index == option_index)]
        voc = Query.en(df.groupby('dub')).to_dictionary(lambda z: z[0], lambda z: z[1].set_index('text').file_name.to_dict())
        return Dubber(voc, self.host_folder)


    def merge_with_latest(self, latest_pack: 'DubbingPack'):
        tasks = list(latest_pack.fragments) + list(self.fragments)

        df = pd.concat([
            latest_pack.df.assign(bigger_order=0),
            self.df.assign(bigger_order=1)
        ]).reset_index(drop=True)

        df['option_index_fix'] = df.bigger_order*1000 + df.option_index
        df = df.feed(fluq.add_ordering_column(['voice','dub','text'], 'option_index_fix', 'option_index_new'))
        for i, ind in zip(df.index, df.option_index_new):
            tasks[i].option_index = ind

        return DubbingPack(tasks)

    @staticmethod
    def create_debugging_dubber(dubs: List[Union[Dub,Template]]):
        fragments = Fragmenter(dubs, []).run('test_voice')
        for f in fragments:
            f.option_index = 0
            f.file_name=f.text
        pack = DubbingPack(fragments)
        return pack.to_dubber('test_voice',0)

    @staticmethod
    def from_folder(folder: Path) -> 'DubbingPack':
        return DubbingPack(
            FileIO.read_pickle(folder/'records.pkl'),
            folder,
            FileIO.read_pickle(folder/'errors.pkl') if (folder/'errors.pkl').is_file() else None
        )

    @staticmethod
    def from_zip(folder: Path, zip_file: Path, *additional_files: Path) -> 'DubbingPack':
        if folder.is_dir():
            shutil.rmtree(folder)
        elif folder.is_file():
            raise ValueError('First argument should be folder')
        os.makedirs(folder)

        zip_files = [zip_file]+list(additional_files)
        packs = []

        for zf in zip_files:
            with zipfile.ZipFile(zf, 'r', zipfile.ZIP_DEFLATED) as zp:
                for name in zp.namelist():
                    stream = zp.open(name)
                    bytes = stream.read()
                    with open(folder/name, 'wb') as out_stream:
                        out_stream.write(bytes)
            packs.append(DubbingPack.from_folder(folder))

        pack = packs[0]
        for p in packs[1:]:
            pack = pack.merge_with_latest(p)
        pack.host_folder = folder
        return pack



    def save_to_zip(self, zip_file, encode = False, with_progress_bar = False):
        _save_dubbing_pack(zip_file, self.fragments, self.errors, self.host_folder, encode, with_progress_bar)