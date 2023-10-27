from pathlib import Path
from yo_fluq_ds import *
from PIL import Image
from .comparison import diversify
import shutil
import os
from .conversion import ConvertImage
import ipywidgets

class Extractor:
    def __init__(self, folder):
        self.folder = folder

    def get_files(self,crop_file):
        base = Path(str(crop_file).replace('.crop.json' ,''))
        yield base
        folder = Path(str(base ) +'.group')
        if folder.is_dir():
            yield from Query.folder(folder)

    def process_all(self):
        rows = []
        images = []
        icons = []
        idx = 0
        for cluster_index, crop_file in (Query
                .folder(self.folder)
                .where(lambda z: z.name.endswith('.crop.json'))
                .feed(list ,Query.en ,fluq.with_progress_bar(), enumerate)
        ):
            crops = FileIO.read_jsonpickle(crop_file)
            for file_index, file in enumerate(self.get_files(crop_file)):
                im = Image.open(file)
                for crop_index, crop in enumerate(crops):
                    if 508<=crop.size and crop.size <=516:
                        crop.size = 512
                        crop = crop.try_put_in_bound(im.width, im.height)
                    c = crop.crop(im)
                    row = Obj(
                        crop_file=crop_file,
                        crop_file_name = crop_file.name,
                        file_name = file.name,
                        file_path = file,

                        cluster_index = cluster_index,
                        file_index=file_index,
                        crop_index = crop_index,

                        group = f'{cluster_index}_{crop_index}',

                        image_size=(c.size[0 ] +c.size[1] ) /2,
                        output = f'{cluster_index}_{crop_index}_{file.name}',

                        idx = idx
                    )
                    rows.append(row)
                    images.append(c)
                    icons.append(c.resize((200 ,200)))
                    idx+=1
        df = pd.DataFrame(rows)
        self.df = df
        self.images = images
        self.icons = icons

    def diversify(self, from_each_group = 5):
        cnt = 5
        div_df = (
            Query
                .en(self.df.group.unique())
                .feed(fluq.with_progress_bar())
                .select(lambda z: diversify(list(self.df.loc[self.df.group == z].idx), self.icons, from_each_group))
                .feed(list, pd.concat)
        )
        rdf = self.df.merge(div_df, left_on='idx', right_index=True, how='left')
        rdf.originality = rdf.originality.fillna(0)
        rdf = rdf.feed(fluq.add_ordering_column('group', ('originality', False), 'boredom'))
        self.df = rdf

    def preview(self, df = None):
        boxes = []
        if df is None:
            df = self.df
        for group in df.group.unique():
            xdf = df.loc[df.group == group]
            ch = [ConvertImage(self.icons[p]).to_pywidget() for p in xdf.idx]
            boxes.append(ipywidgets.HBox(ch))
        return ipywidgets.VBox(boxes)



    def save(self, folder, df = None):
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder)
        if df is None:
            df = self.df
        for row in Query.df(df):
            self.images[row['idx']].resize((512,512)).save(folder/row['output'])
