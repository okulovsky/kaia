from typing import *
from kaia.brainbox import BrainBoxTask, MediaLibrary, BrainBoxApi
from kaia.brainbox.deciders import Collector
from yo_fluq_ds import *
from .image_tools import ConvertImage
from ipywidgets import HTML




class Preview:
    def __init__(self,
                 partition_by_columns: list[str],
                 sort_by_columns: list[str],
                 output_columns:  list[str]|None = None,
                 preview_size: int = 200
                 ):
        self.partition_by_columns = list(partition_by_columns)
        self.sort_by_columns = list(sort_by_columns)
        self.output_columns = output_columns
        self.preview_size = preview_size


    def draw(self, ml: MediaLibrary):
        df = ml.to_df()
        df = df.sort_values(self.partition_by_columns+self.sort_by_columns)
        old_row = None
        html = []
        for row in Query.df(df):
            for index, column in enumerate(self.partition_by_columns):
                if old_row is None or old_row[column] != row[column]:
                    html.append(f'<h{index+1}>{row[column]}</h{index+1}>')
            old_row = row

            title = ''
            for column in self.output_columns:
                title+=f"{column}: {row[column]} "

            html.append(
                ConvertImage(ml[row['filename']].get_content())
                .resize_to_bounding(self.preview_size)
                .to_html_tag(additional_attributes=f'title="{title}"'))

        return HTML(''.join(html))

    def download_and_draw(self, api: BrainBoxApi, id: str):
        ml = MediaLibrary.read(api.download(api.get_result(id)))
        return self.draw(ml)





