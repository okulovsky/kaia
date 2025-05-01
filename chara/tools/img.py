from brainbox import File
from pathlib import Path
from PIL import Image
import io
import base64
import ipywidgets
from yo_fluq import Query, fluq
from typing import *
from dataclasses import dataclass
from brainbox import MediaLibrary


class Img:
    def __init__(self,
                 image: str|Path|Image.Image|bytes|bytearray|File,
                 caption: str = None
                 ):
        self.caption = ''
        if isinstance(image, Path) or isinstance(image, str):
            self.image = Image.open(image)
            self.caption = Path(image).name
        elif isinstance(image, bytes) or isinstance(image, bytearray):
            bts = io.BytesIO(image)
            self.image = Image.open(bts)
        elif isinstance(image, File):
            bts = io.BytesIO(image.content)
            self.image = Image.open(bts)
            self.caption = image.name
        elif isinstance(image, Image.Image):
            self.image = image
        elif isinstance(image, Img):
            self.image = image.image
            self.caption = image.caption
        else:
            raise TypeError(f"Unexpected type {type(image)}")

        if caption is not None:
            self.caption = caption

    def resize(self, bounding_width: int, bounding_height: int | None = None) -> 'Img':
        if bounding_height is None:
            bounding_height = bounding_width
        ratio_w = bounding_width / self.image.width
        ratio_h = bounding_height / self.image.height
        ratio = min(ratio_w, ratio_h)
        new_image = self.image.resize((int(ratio * self.image.width), int(ratio * self.image.height)))
        return Img(new_image, self.caption)

    def resize_exact(self, width: int, height: int) -> 'Img':
        image = self.image.resize((width, height))
        return Img(image, self.caption)

    def _to_bytes(self) -> bytes:
        bio = io.BytesIO()
        self.image.save(bio, 'PNG')
        return bio.getvalue()

    def to_bytes(self) -> bytes:
        return self._to_bytes()

    def to_base64(self) -> str:
        return base64.b64encode(self.to_bytes()).decode('utf-8')

    def to_html(self, additional_attributes='') -> str:
        return f'<img src="data:image/png;base64, {self.to_base64()}" {additional_attributes}/>'

    def to_pil(self) -> Image.Image:
        return self.image

    def to_pywidget(self):
        widget = ipywidgets.Image(value=self._to_bytes())
        if self.caption is None:
            return widget
        else:
            return ipywidgets.VBox([widget, ipywidgets.Label(self.caption)])

    @staticmethod
    def open(data) -> Union['Img','Imgs']:
        img = _try_create_img(data, None, False, None)
        if img is not None:
            return img
        return Imgs(data)

    Type = str|Path|Image.Image|bytes|bytearray|File
    Many: 'type[Imgs]' = None
    Drawer: 'type[Drawer]' = None





def _try_create_img(data, caption, do_raise, details: str|None) -> Img|None:
    try:
        return Img(data, caption)
    except TypeError as ex:
        if not do_raise:
            return None
        if details is None:
            raise
        raise TypeError(f"Cannot create img {details}") from ex


class Imgs:
    def __init__(self, data):
        img = _try_create_img(data, None, False, None)
        if img is not None:
            self.images = [img]
            return
        if isinstance(data, dict):
            self.images = []
            for key, value in data.items():
                self.images.append(_try_create_img(value, key, True, f"at key {key}"))
        else:
            try:
                data = list(data)
            except:
                raise ValueError("Expected Img-convertible, dict or list")
            self.images = []
            for index, element in enumerate(data):
                self.images.append(_try_create_img(element,None,True, f"at index {index}"))

    def resize(self, bounding_width: int, bounding_height: int | None = None) -> 'Imgs':
        return Imgs(im.resize(bounding_width, bounding_height) for im in self.images)

    def resize_exact(self, width: int, height: int) -> 'Imgs':
        return Imgs(im.resize_exact(width, height) for im in self.images)

    def to_pywidget(self, columns: int|None = 5):
        widgets = [im.to_pywidget() for im in self.images]
        if columns is None:
            return ipywidgets.HBox(widgets)
        return (
            Query
            .en(widgets)
            .feed(fluq.partition_by_count(columns))
            .select(lambda z: ipywidgets.HBox(z))
            .feed(list,ipywidgets.VBox)
        )



class Drawer:
    @dataclass
    class Item:
        source: Any
        img: Img


    def __init__(self, images: Iterable, columns=5, resize=300):
        self._images = list(images)
        self._columns = columns
        self._resize = resize
        self._retriever: Optional[Callable[[Any], Img.Type]] = None

    def retrieve(self, function: Callable[[Any], Img.Type]) -> 'Drawer':
        self._retriever = function
        return self

    def _draw_internal(self, images: list['Drawer.Item'], selectors: list, level):
        if len(selectors) == 0:
            return Img.Many(item.img for item in images).to_pywidget(self._columns)
        selector = lambda z: selectors[0](z.source)
        if len(selectors) == 1:
            return (
                Query
                .en(images)
                .order_by(selector)
                .select(lambda z: Img(z.img, str(selector(z))))
                .feed(Img.Many)
                .to_pywidget(self._columns)
            )
        rows = []
        for group in Query.en(images).group_by(selector).order_by(lambda z: z.key):
            rows.append(ipywidgets.HTML(f'<h{level}>{group.key}</h{level}>'))
            rows.append(self._draw_internal(group.value, selectors[1:], level+1))
        return ipywidgets.VBox(rows)

    def draw(self, *selectors):
        items = []
        for src in self._images:
            if self._retriever is not None:
                items.append(Drawer.Item(src, Img(self._retriever(src))))
            else:
                items.append(Drawer.Item(src, Img(src)))
        return self._draw_internal(items, list(selectors), 1)



Img.Many = Imgs
Img.Drawer = Drawer