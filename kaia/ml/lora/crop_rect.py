from dataclasses import dataclass, field
import math
import shapely
from PIL import ImageDraw
from PIL.Image import Image
import PIL
from copy import copy
from uuid import uuid4


@dataclass
class CropRect:
    center_x: float
    center_y: int
    size: float = 200
    angle: float = 0
    uuid: str = field(default_factory=lambda: str(uuid4()))

    def scale(self, scale) -> 'CropRect':
        return CropRect(
            int(self.center_x*scale),
            int(self.center_y*scale),
            int(self.size*scale),
            self.angle,
            self.uuid
        )


    def get_locs(self):
        R = self.size/2
        res = []
        for i in range(4):
            a = (90*i+self.angle)*math.pi/180
            x = self.center_x+R*math.cos(a)-R*math.sin(a)
            y = self.center_y+R*math.sin(a)+R*math.cos(a)
            res.append((x,y))
        return res

    def get_bounding(self):
        locs = self.get_locs()
        xmin = min(p[0] for p in locs)
        ymin = min(p[1] for p in locs)
        xmax = max(p[0] for p in locs)
        ymax = max(p[1] for p in locs)
        return xmin, ymin, xmax, ymax

    def try_put_in_bound(self, width, height):
        rect = copy(self)
        x0, y0, x1, y1 = rect.get_bounding()
        if x0<0:
            rect.center_x+=-x0+1
        elif x1>=width:
            rect.center_x-=(x1-width+1)
        if y0<0:
            rect.center_y+=-y0+1
        elif y1>=height:
            rect.center_y-=(y1-height+1)
        return rect

    def is_bounded(self, width, height):
        x0, y0, x1, y1 = self.get_bounding()
        return x0>=0 and y0>=0 and x1<width and y1<height


    def contains(self, x, y):
        point = shapely.Point(x, y)
        polygon = shapely.Polygon(self.get_locs())
        return polygon.contains(point)

    def draw(self, image:Image, color):
        points = self.get_locs()
        draw = ImageDraw.Draw(image)
        for i in range(4):
            p1 = points[i]
            p2 = points[(i+1)%4]
            draw.line(p1+p2, fill=color, width = 3)

    def crop(self, image:Image):
        resultIm = image.rotate(self.angle, center=(self.center_x, self.center_y), resample=PIL.Image.BICUBIC)
        left = self.center_x - self.size // 2
        top = self.center_y - self.size // 2
        return resultIm.crop((int(left), int(top), int(left + self.size), int(top + self.size)))