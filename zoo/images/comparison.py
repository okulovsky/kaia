from yo_fluq_ds import *
import numpy as np
from PIL import Image

def get_distance(im1, im2):
    im1 = im1.convert('RGB')
    im2 = im2.convert('RGB')
    return (np.asarray(im1) - np.asarray(im2)).mean()

def compare_images(cmp_task):
    id1 = cmp_task['id_1']
    id2 = cmp_task['id_2']
    image1 = Image.open(id1) if 'image_1' not in cmp_task else cmp_task['image_1']
    image2 = Image.open(id2) if 'image_2' not in cmp_task else cmp_task['image_2']
    dst = get_distance(image1, image2)
    return dict(id_1 = id1, id_2 = id2, distance=dst)


def diversify(group, icons, cnt):
    if len(group) == 1:
        return pd.DataFrame([dict(idx=group[0], originality=1000)])

    mp = (Query
          .combinatorics
          .triangle(group, with_diagonal=False)
          .select(lambda z: Obj(id_1=z[0], id_2=z[1], image_1=icons[z[0]], image_2=icons[z[1]]))
          .select(compare_images)
          .select_many(lambda z: [z, dict(id_1=z['id_2'], id_2=z['id_1'], distance=z['distance'])])
          .to_dictionary(lambda z: (z['id_1'], z['id_2']), lambda z: z['distance'])
          )

    pair = Query.dict(mp).argmax(lambda z: z.value)
    winners = {z: pair.value for z in pair.key}
    candidates = set(z for z in group if z not in winners)

    while len(winners) < cnt and len(candidates) > 0:
        winner = Query.en(candidates).select(lambda z: (z, Query.en(winners).min(lambda x: mp[(z, x)]))).argmax(
            lambda z: z[1])
        winners[winner[0]] = winner[1]
        candidates.remove(winner[0])
    return pd.Series(winners).to_frame('originality')