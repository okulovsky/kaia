from resemblyzer import preprocess_wav, VoiceEncoder
from itertools import groupby
from pathlib import Path
from tqdm import tqdm
import numpy as np
import pandas as pd



class WavProcessor:
    def __init__(self):
        self.encoder = VoiceEncoder()

    def get_encoding(self, wav_path: Path):
        preprocessed = preprocess_wav(wav_path)
        encoding = self.encoder.embed_utterance(preprocessed)
        return encoding

    def get_encodings(self, path: Path):
        encodings = {}
        wavs = list(path.glob('**/*.wav'))
        for wav in tqdm(wavs, f'Folder {path.parent.name}', len(wavs)):
            speaker_name = wav.parent.name
            if speaker_name not in encodings:
                encodings[speaker_name] = []
            encodings[speaker_name].append(self.get_encoding(wav))
        return encodings



class Model:
    def __init__(self, embeddings, accuracy = -1, stats = None):
        self.embeddings = embeddings
        self.accuracy = accuracy
        self.stats: None|pd.DataFrame = stats

    def compute_winner(self, embedding):
        winner = None
        winner_score = None

        for key, value in self.embeddings.items():
            score = max(np.inner(embedding, value))
            if winner is None or score > winner_score:
                winner = key
                winner_score = score
        return winner

    def compute_full(self, embedding):
        rows = []
        for key, value in self.embeddings.items():
            for i, score in enumerate(np.inner(embedding, value)):
                rows.append(dict(speaker=key, sample_index=i, score=float(score)))
        return rows

    def evaluate(self, test):
        dfs = []
        total = 0
        matches = 0
        for key, samples in test.items():
            for i, sample in enumerate(samples):
                rows = self.compute_full(sample)
                df = pd.DataFrame(rows)
                df = df.sort_values('score', ascending=False)
                df['order'] = list(range(df.shape[0]))
                df['true_speaker'] = key
                df['source_sample_index'] = i
                dfs.append(df)

                winner = self.compute_winner(sample)
                if winner == key:
                    matches += 1
                total += 1

        if total > 0:
            self.stats = pd.concat(dfs)
            self.accuracy = matches / total
        else:
            self.stats = None
            self.accuracy = None


