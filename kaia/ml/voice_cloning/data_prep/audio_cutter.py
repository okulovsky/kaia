from scipy.io import wavfile
from pathlib import Path
from yo_fluq_ds import *
import os
import shutil
from matplotlib import pyplot as plt

class AudioCutter:
    def __init__(self, path):
        self.path = Path(path)
        if self.path.name.endswith('.wav'):
            self.wav_path = self.path
        else:
            self.wav_path = self.path.parent / (self.path.name.split('.')[0] + '.wav')
        self.output_path = Path(str(self.wav_path) + '.output')

    def read(self):
        if self.wav_path != self.path:
            os.system(f'ffmpeg -i {self.path} {self.wav_path}')
        [sample_rate, data] = wavfile.read(self.wav_path, 'r')
        df = pd.DataFrame(data)
        df = df[[0]]
        df.columns = ['signal']
        df['time'] = df.index / sample_rate
        return df

    def find_silence(self, df, threshold=10):
        res = []
        for s in df.signal.abs():
            if s < threshold:
                if len(res) == 0:
                    res.append(1)
                else:
                    res.append(res[-1] + 1)
            else:
                res.append(0)

        cm = [0 for _ in range(len(res))]

        for i in range(len(res) - 1, -1, -1):
            if i < len(res) - 1 and res[i] == res[i + 1] - 1:
                cm[i] = cm[i + 1]
            else:
                cm[i] = res[i]

        df['silence'] = cm
        return df

    def create_trim_table(self, df, threshold=1000):
        xdf = df.loc[df.silence < threshold].copy()
        xdf['this_id'] = xdf.index
        xdf['prev_id'] = xdf.this_id.shift(1)
        xdf['new_id'] = (xdf.this_id - xdf.prev_id) > 1.1
        xdf['chunk'] = xdf.new_id.cumsum()
        limits = xdf.groupby('chunk').time.aggregate(['min', 'max'])
        return limits

    def plots(self, df):
        _, ax = plt.subplots(1, 2, figsize=(20, 7))
        df.signal.plot(ax=ax[0])
        df.silence.plot(ax=ax[1])

    def extract(self, limits):
        shutil.rmtree(self.output_path, ignore_errors=True)
        os.makedirs(self.output_path)

        for i, chunk in Query.df(limits).feed(enumerate):
            start = round(chunk.min, 3)
            ln = round(chunk.max - chunk.min, 3)
            cmd = f'ffmpeg -i {self.wav_path} -ss {start} -t {ln} -c copy {self.output_path / (str(i) + ".wav")}'
            os.system(cmd)

    def make_all(self):
        df = self.read()
        self.find_silence(df)
        self.plots(df)
        limits = self.create_trim_table(df)
        self.extract(limits)




