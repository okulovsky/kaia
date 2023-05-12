import ipywidgets
from yo_fluq_ds import *
from PIL import Image
from .comparison import compare_images
from .conversion import ConvertImage
import shutil
from scipy.cluster.hierarchy import dendrogram, linkage, cut_tree




class Clusterizer:
    def __init__(self, folder, workers_count = 5):
        self.folder = folder
        self.workers_count = workers_count


    def compute(self):
        files = [c.name for c in Query.folder(self.folder) if not c.name.endswith('json')]
        self.pdf = pd.DataFrame(dict(path=files))
        self.icons = Query.en(files).to_dictionary(lambda z: z, lambda z: Image.open(self.folder/z).resize((200,200)))
        comparison_tasks = (Query
                            .combinatorics
                            .triangle(files, False)
                            .select(lambda z: Obj(id_1=z[0], id_2=z[1], image_1=self.icons[z[0]], image_2=self.icons[z[1]]))
                            .to_list()
                            )
        self.df = (
            Query
                .en(comparison_tasks)
                .parallel_select(compare_images, workers_count=self.workers_count)
                .feed(fluq.with_progress_bar())
                .to_dataframe()
        )
        self.linkage =  linkage(self.df.distance)

    def dendrogram(self):
        return dendrogram(self.linkage)

    def cut(self, height):
        classes = cut_tree(self.linkage, height=30)[:, 0]
        self.pdf['cluster'] = classes

    def preview(self):
        boxes = []
        for cluster in self.pdf.cluster.unique():
            xdf = self.pdf.loc[self.pdf.cluster == cluster]
            ch = [ConvertImage(self.icons[p]).to_pywidget() for p in xdf.path]
            boxes.append(ipywidgets.HBox(ch))
        return ipywidgets.VBox(boxes)

    def save(self, folder, overwrite = True):
        if overwrite:
            shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder, exist_ok=True)
        for i, c in enumerate(self.pdf.cluster.unique()):
            files = self.pdf.loc[self.pdf.cluster == c].path.sort_values().feed(list)
            main = files[0]
            shutil.copyfile(self.folder/files[0], folder / main)
            if len(files) > 1:
                d = folder / f'{main}.group'
                os.makedirs(d, exist_ok=True)
                for file in files[1:]:
                    shutil.copyfile(self.folder/file, d / file)





