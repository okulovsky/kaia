
from PIL import Image, ImageDraw, ImageFont
from kaia.infra.ffmpeg import FFmpegTools
import shutil
import os
from yo_fluq_ds import *
from kaia.infra import Loc


def create_image(size, bgColor, message, fontColor):
    font = ImageFont.truetype("arial.ttf", 100)
    W, H = size
    image = Image.new('RGB', size, bgColor)
    draw = ImageDraw.Draw(image)
    _, _, w, h = draw.textbbox((0, 0), message, font=font)
    draw.text(((W-w)/2, (H-h)/2), message, font=font, fill=fontColor)
    return image


def make_all(path):
    files = Query.folder(path).select(lambda z: z.name).select(lambda z: [z] + z.split('.')[0].split('_')).to_list()
    data = {}

    out_path = path.parent / 'qavid'
    shutil.rmtree(out_path, ignore_errors=True)
    os.makedirs(out_path)

    for file in Query.en(files).feed(fluq.with_progress_bar()):
        if file[1] != 'sample' or not file[0].endswith('wav'):
            continue
        im = create_image((640, 480), 'black', file[-1], 'white')
        im_name = file[0].replace('.wav', '.png')
        im.save(out_path / im_name)
        mp4_name = file[0].replace('.wav', '.mpeg')
        FFmpegTools.make_video_from_audio_and_image(out_path / im_name, path / file[0], out_path / mp4_name)
        if file[-2] not in data:
            data[file[-2]] = {}
        data[file[-2]][int(file[-1])] = mp4_name

    for voice in data:
        flist = [out_path / data[voice][f] for f in sorted(data[voice])]
        FFmpegTools.concat_audio_with_ffmpeg(flist, out_path / f'all_{voice}.mpeg')