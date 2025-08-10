import os
import shutil
import traceback
from pathlib import Path
from .steps import IStepFactory, IStep
from yo_fluq import *
import dill

def write_dill(obj, path):
    with open(path, 'wb') as f:
        dill.dump(obj, f)

def read_dill(path):
    with open(path, 'rb') as f:
        return dill.load(f)


class Flow:
    def __init__(self,
                 folder: Path|str,
                 steps: list[IStep|IStepFactory]|None = None,
                 prehistory: list|None = None
                 ):
        self.folder = Path(folder)
        if prehistory is None:
            prehistory = []
        self.prehistory = prehistory
        if steps is not None:
            self.steps = []
            for i, s in enumerate(steps):
                if isinstance(s, IStep):
                    self.steps.append(s)
                elif isinstance(s, IStepFactory):
                    self.steps.append(s.create_step())
                else:
                    raise ValueError(f"Erroneous step #{i}: must be IStep or IStepFactory, but was {type(s)}")
        else:
            self.steps = None

    def reset(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def _run_stages(self, iteration_index, history):
        current = []
        for stage_index, stage in enumerate(self.steps):
            name = stage.get_name()
            if name is None:
                name = type(stage).__name__
            print(f"{len(current)} records -> Start {name}, {stage_index}/{len(self.steps)} -> ", end='')
            full = None
            short = None
            try:
                full = stage.process(self.prehistory+history, current)
                short = stage.shorten(full)
                report = dict(index=stage_index, name=name, input=current, full_output=full, short_output=short, error = None)
                write_dill(report, self.folder/f'fulls/{iteration_index}_{stage_index}')
                summary = stage.summarize(full)
                if summary is not None:
                    summary = f' ({summary})'
                else:
                    summary = ''
                current = short
                print(f'{len(current)} records{summary}')
            except:
                print()
                report = dict(index=stage_index, name=name, input=current, full_output=full, short_output=short, error=traceback.format_exc())
                write_dill(report, self.folder / f'fulls/{iteration_index}_{stage_index}')
                raise

        write_dill(current, self.folder / f'results/{iteration_index}')
        return current


    def run(self, iterations):
        os.makedirs(self.folder / 'fulls', exist_ok=True)
        os.makedirs(self.folder / 'results', exist_ok=True)
        existing_files = Query.folder(self.folder/'results').to_list()
        existing = Query.en(existing_files).select_many(read_dill).to_list()
        print(f'TOTAL {len(existing)}')
        if len(existing_files) == 0:
            existing_index = -1
        else:
            existing_index = Query.en(existing_files).select(lambda z: int(z.name)).max()
        for index in range(existing_index+1, existing_index+1+iterations):
            result = self._run_stages(index, existing)
            existing.extend(result)
            print(f'TOTAL {len(existing)}')




    def read_iterations_count(self):
        index = 0
        while True:
            path = self.folder / f'results/{index}'
            if not path.is_file():
                return index-1
            index+=1


    def read_flatten(self):
        return Query.folder(self.folder/'results').where(lambda z: z.is_file()).order_by(lambda z: int(z.name)).select_many(read_dill).to_list()

    def read_debug_report(self, iteration: int, stage: int):
        return read_dill(self.folder/f'fulls/{iteration}_{stage}')


