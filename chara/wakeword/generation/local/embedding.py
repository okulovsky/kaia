# Copyright 2022 David Scripka. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Imports

import numpy as np
from numpy.lib.format import open_memmap
from tqdm import tqdm


def compute_features_from_generator(
    generator,
    n_total,
    clip_duration,
    output_file,
    device="cpu",
    ncpu=1,
    model_paths=None,
):
    """
    Computes audio features from a generator that produces Numpy arrays of shape (batch_size, samples)
    containing 16-bit PCM audio data.

    Args:
        generator (Generator): The generator that process the arrays of audio data
        n_total (int): The total number of rows (audio clips) that the generator will produce.
                       Ideally this is precise, but it can be approximate as well as the output
                       .npy file will be automatically trimmed to remove empty values.
        clip_duration (float): The duration (in samples) of the audio produced by the generator
        output_file (str): The output file (.npy) containing the audio features. Note that this file
                           will be written to using memmap arrays, so it can be substantially larger
                           than the available system memory.
        device (str): The device ("cpu" or "gpu") to use for computing features.
        ncpu (int): The number of cores to use when process the audio features (if computing on CPU)

    Returns:
        None
    """
    # Function specific imports
    # Windows-safe trimming is implemented below.

    # Create audio features object
    from openwakeword.utils import AudioFeatures

    F = AudioFeatures(
        device=device,
        ncpu=ncpu,
        melspec_model_path=model_paths["melspectrogram.onnx"],
        embedding_model_path=model_paths["embedding_model.onnx"],
    )

    # Determine the output shape and create output file
    n_feature_cols = F.get_embedding_shape(clip_duration / 16000)
    output_shape = (n_total, n_feature_cols[0], n_feature_cols[1])
    fp = open_memmap(output_file, mode="w+", dtype=np.float32, shape=output_shape)

    # Get batch size by pulling one value from the generator and store features
    row_counter = 0
    audio_data = next(generator)
    batch_size = audio_data.shape[0]

    if batch_size > n_total:
        raise ValueError(
            f"The value of 'n_total' ({n_total}) is less than the batch size ({batch_size})."
            " Please increase 'n_total' to be >= batch size."
        )

    features = F.embed_clips(audio_data, batch_size=batch_size)
    fp[row_counter : row_counter + features.shape[0], :, :] = features
    row_counter += features.shape[0]
    fp.flush()

    # Compute features and add data to output file
    for audio_data in tqdm(
        generator, total=n_total // batch_size, desc="Computing features"
    ):
        if row_counter >= n_total:
            break

        features = F.embed_clips(audio_data, batch_size=batch_size, ncpu=ncpu)
        if row_counter + features.shape[0] > n_total:
            features = features[0 : n_total - row_counter]

        fp[row_counter : row_counter + features.shape[0], :, :] = features
        row_counter += features.shape[0]
        fp.flush()

    # Trip empty rows from the mmapped array
    del fp
    trim_mmap(output_file)


def trim_mmap(path):
    from pathlib import Path

    path = Path(path)
    data = np.load(path, mmap_mode="r", allow_pickle=False)
    count = len(data)
    while count and not np.any(data[count - 1]):
        count -= 1
    if not count:
        del data
        raise ValueError("embedding model produced no nonzero feature rows")
    if count == len(data):
        del data
        return
    target = path.with_name(path.name + ".trim.npy")
    output = open_memmap(
        target, mode="w+", dtype=data.dtype, shape=(count, *data.shape[1:])
    )
    for start in range(0, count, 256):
        output[start : start + 256] = data[start : min(start + 256, count)]
    output.flush()
    del output, data
    target.replace(path)
