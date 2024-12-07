import os
from pathlib import Path
import pandas as pd
from log_parsing import parse
from matplotlib import pyplot as plt
from service import Service
from utils import get_working_folder

class Drawer(Service):
    def __init__(self,
                 folder: Path,
                 sleep_in_seconds: int = 60
                 ):
        super().__init__(folder, sleep_in_seconds)


    def build_dataframes(self, models_folder):
        parsed = parse(models_folder / 'trainer_0_log.txt')

        df = pd.DataFrame(
            [dict(iteration=z.iteration, rel_epoch=z.epoch, step=z.step) for z in parsed]
        )
        df['epoch'] = list(range(df.shape[0]))
        step_to_epoch = (df.step / (df.epoch + 1)).mean()

        tdf = pd.DataFrame([z.train_metrics for z in parsed])
        tdf = tdf.dropna()
        tdf.index *= int(step_to_epoch)


        for c in tdf.columns:
            tdf[c] = tdf[c] / tdf[c].mean()

        fig, ax = plt.subplots(1, 1, figsize=(15, 7))
        tdf.rolling(10).mean()[[c for c in tdf.columns if 'loss' in c]].plot(ax=ax)
        return df, tdf, fig



    def _iteration(self):
        models_folder = get_working_folder(self.folder)
        if models_folder is None:
            return
        _, __, fig = self.build_dataframes(models_folder)
        fig.savefig(self.folder.parent/'plot.png')


