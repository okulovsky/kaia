import subprocess
from typing import *
from ...core import IDecider
from copy import copy
import traceback
import torch
from uuid import uuid4
import torchaudio
from abc import ABC, abstractmethod
import zipfile
import pickle
from ....infra import Loc
import os
from yo_fluq_ds import *

class IDubCollectorProcessor(ABC):
    @abstractmethod
    def cut(self, file, start, length):
        pass

    @abstractmethod
    def postprocess(self,records, errors):
        pass

    def set_file_cache(self, file_cache):
        self.file_cache = file_cache


class FakeDubCollectorProcessor(IDubCollectorProcessor):
    def cut(self, file, start, length):
        return file[start:start + length]

    def postprocess(self,records, errors):
        return dict(records=records, errors=errors)


def recode_file(host_folder, r):
    if os.path.getsize(host_folder/r.file_name) < 1000:
        return
    target = r.file_name.replace('.wav', '.ogg')
    result = subprocess.call([
        Loc.get_ffmpeg(),
        '-i',
        str(host_folder / r.file_name),
        '-c:a',
        'libvorbis',
        '-b:a',
        '64k',
        str(host_folder / target)
    ])
    if result != 0:
        raise ValueError(f'Cannot encode file {r.file_name}')
    r.file_name = target




def _save_dubbing_pack(
        zip_file,
        tasks,
        errors,
        host_folder,
        encode = False,
        with_progress_bar = False
):
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zp:

        if with_progress_bar:
            q_tasks = Query.en(tasks).feed(fluq.with_progress_bar())

        for r in q_tasks:
            if encode:
                recode_file(host_folder, r)
            with open(host_folder / r.file_name, 'rb') as f:
                bts = f.read()
                zp.writestr(r.file_name, bts)

        zp.writestr('records.pkl', pickle.dumps(tasks))
        zp.writestr('errors.pkl', pickle.dumps(errors))





class TortoiseTTSDubCollectorPostprocessor(IDubCollectorProcessor):
    def cut(self, file, start, length):
        data = torch.load(self.file_cache / file)
        start_alignment = data['alignment'][start]
        end_alignment = data['alignment'][start + length - 1]
        audio_clip = data['audio'][:, :, start_alignment:end_alignment]
        wav_file = str(uuid4()) + ".wav"
        torchaudio.save(self.file_cache / wav_file, audio_clip.squeeze(0).cpu(), 24000)
        return wav_file


    def postprocess(self,records, errors):
        zip_file = self.file_cache/f'{uuid4()}.zip'
        _save_dubbing_pack(zip_file, records, errors, self.file_cache, True, True)
        return zip_file.name



class DubCollector(IDecider):
    def __init__(self, processor: Optional[IDubCollectorProcessor] = None):
        self.processor = processor if processor is not None else TortoiseTTSDubCollectorPostprocessor()

    def warmup(self):
        pass

    def cooldown(self):
        pass

    def collect(self, spec: Dict[str, List], **kwargs):
        self.processor.set_file_cache(self.file_cache)
        errors = []
        records = []
        for id, desc in spec.items():
            if id not in kwargs:
                errors.append(f'Id {id} not in the list of jobs')
            result = kwargs[id]
            for cut_index, cut in enumerate(desc):
                for file_index, file in enumerate(result):
                    try:
                        cut_file = self.processor.cut(file, cut.start, cut.length)
                    except:
                        errors.append(f"Error when processing id {id}, cut_index {cut_index}, file_index {file_index}\n{traceback.format_exc()}")
                        continue

                    record = copy(cut.info)
                    record.file_name = cut_file
                    record.option_index = file_index
                    records.append(record)
        return self.processor.postprocess(records, errors)











