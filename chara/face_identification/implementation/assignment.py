import os

import pandas as pd
from dataclasses import dataclass
from chara.tools import Img
import numpy as np
from yo_fluq import fluq, Query
from avatar.server import AvatarApi
from pathlib import Path
import shutil
from yo_fluq import FileIO

@dataclass
class Assignment:
    avatar_api: AvatarApi
    df: pd.DataFrame


    def browse(self, cnt_per_cluster:int = 10):
        df = self.df.assign(rnd = np.random.rand(self.df.shape[0]))
        df = df.feed(fluq.add_ordering_column('cluster', 'rnd'))
        df = df.loc[df.order < cnt_per_cluster]
        return (
            Img
            .Drawer(Query.df(df).to_list())
            .retrieve(lambda z: Img(self.avatar_api.file_cache.download(z.name)))
            .draw(lambda z: z.cluster, lambda z: z.name)
        )

    def export(self, folder: Path, name_to_clusters: dict[str, list[int]], samples_per_name: int):
        df = self.df.assign(class_name = None)
        for name, clusters in name_to_clusters.items():
            for cluster in clusters:
                df.loc[df.cluster==cluster,'class_name'] = name
        df = df.loc[~df.class_name.isnull()]
        df = df.assign(rnd = np.random.rand(df.shape[0]))
        df = df.feed(fluq.add_ordering_column('class_name', 'rnd'))
        df = df.loc[df.order < samples_per_name]

        shutil.rmtree(folder, ignore_errors=True)
        for row in Query.df(df):
            target = folder/row.class_name/row.name
            os.makedirs(target.parent, exist_ok=True)
            FileIO.write_bytes(
                self.avatar_api.file_cache.download(row.name),
                target
            )










