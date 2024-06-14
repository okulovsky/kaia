from utils import read_media_library
import shutil
import os
import subprocess
from pathlib import Path
from TTS.bin.resample import resample_files
from dataclasses import dataclass
from TTS.bin.compute_embeddings import compute_embeddings
from TTS.tts.utils.languages import LanguageManager
from TTS.tts.utils.speakers import SpeakerManager
from TTS.tts.datasets import load_tts_samples

def media_library_to_vctk_format(
        media_library_path: Path,
        dataset_path: Path,
        temp_path: Path,
        sample_rate: int
):
    shutil.rmtree(dataset_path, ignore_errors=True)
    os.makedirs(temp_path, exist_ok=True)

    for record in read_media_library(media_library_path):
        wav_path = dataset_path / 'wav48_silence_trimmed' / record.voice / (record.filename + '_mic1.flac')
        os.makedirs(wav_path.parent, exist_ok=True)

        full_src_path = temp_path / record.filename
        with open(full_src_path, 'wb') as base_file:
            base_file.write(record.content)

        tmp_file = str(full_src_path).replace('.wav', '.ogg')
        subprocess.call(['ffmpeg', '-i', full_src_path, tmp_file])
        subprocess.call(['ffmpeg', '-i', tmp_file, '-ar', str(sample_rate), '-ac', '1', wav_path])

        txt_file = dataset_path / 'txt' / record.voice / (record.filename + '.txt')
        os.makedirs(txt_file.parent, exist_ok=True)
        with open(txt_file, 'w', encoding='utf-8') as file:
            file.write(record.text)

    resample_files(str(dataset_path), sample_rate, file_ext='flac', n_jobs=8)


@dataclass
class SpeakersEncodings:
    SPEAKER_ENCODER_CHECKPOINT_PATH : str
    SPEAKER_ENCODER_CONFIG_PATH: str
    D_VECTOR_FILES: list[str]


def compute_speaker_encodings(config_list, with_eval) -> SpeakersEncodings:
    ## Extract speaker embeddings
    SPEAKER_ENCODER_CHECKPOINT_PATH = (
        "https://github.com/coqui-ai/TTS/releases/download/speaker_encoder_model/model_se.pth.tar"
    )

    SPEAKER_ENCODER_CONFIG_PATH = "https://github.com/coqui-ai/TTS/releases/download/speaker_encoder_model/config_se.json"
    D_VECTOR_FILES = []  # List of speaker embeddings/d-vectors to be used during the training
    for dataset_conf in config_list:
        # Check if the embeddings weren't already computed, if not compute it
        embeddings_file = os.path.join(dataset_conf.path, "speakers.pth")
        if not os.path.isfile(embeddings_file):
            print(f">>> Computing the speaker embeddings for the {dataset_conf.dataset_name} dataset")
            # print(SPEAKER_ENCODER_CHECKPOINT_PATH)
            # print(SPEAKER_ENCODER_CONFIG_PATH)
            # print(embeddings_file)
            # print(dataset_conf.formatter)
            # print(dataset_conf.dataset_name)
            # print(dataset_conf.path)
            # print(dataset_conf.meta_file_train)
            # print(dataset_conf.meta_file_val)
            compute_embeddings(
                SPEAKER_ENCODER_CHECKPOINT_PATH,
                SPEAKER_ENCODER_CONFIG_PATH,
                embeddings_file,
                old_speakers_file=None,
                config_dataset_path=None,
                formatter_name=dataset_conf.formatter,
                dataset_name=dataset_conf.dataset_name,
                dataset_path=dataset_conf.path,
                meta_file_train=dataset_conf.meta_file_train,
                meta_file_val=dataset_conf.meta_file_val,
                disable_cuda=False,
                no_eval=not with_eval,
            )
        D_VECTOR_FILES.append(embeddings_file)

    return SpeakersEncodings(
        SPEAKER_ENCODER_CHECKPOINT_PATH,
        SPEAKER_ENCODER_CONFIG_PATH,
        D_VECTOR_FILES
    )



@dataclass
class TrainEvalSamples:
    train_samples: list
    eval_samples: list

def process_speaker_manager(
        encodings: SpeakersEncodings,
        config,
        datasets_path: Path,
        model_path: Path,
        with_eval: bool
):
    # @title
    speaker_manager = SpeakerManager(
        d_vectors_file_path=encodings.D_VECTOR_FILES,
        encoder_model_path=encodings.SPEAKER_ENCODER_CHECKPOINT_PATH,
        encoder_config_path=encodings.SPEAKER_ENCODER_CONFIG_PATH
    )

    print("Speakers: " + str(speaker_manager.get_speakers()))
    speaker_manager.save_ids_to_file(str(datasets_path/"speaker_ids.json"))
    #print("Speaker IDs written to: " + self.VCTK_DOWNLOAD_PATH + "/speaker_ids.json")
    speaker_manager.save_embeddings_to_file(str(datasets_path/'speakers.json'))
    #print("Speaker embeddings saved to: " + self.VCTK_DOWNLOAD_PATH + "/speakers.json")
    language_manager = LanguageManager(config=config)
    config.model_args.num_languages = language_manager.num_languages
    print(str(language_manager.num_languages) + " languages found")
    language_manager.save_ids_to_file(str(datasets_path/"language_ids.json"))
    #print("Language IDs written to: " + self.VCTK_DOWNLOAD_PATH + "/language_ids.json")
    # Load all the datasets samples and split traning and evaluation sets
    train_samples, eval_samples = load_tts_samples(
        config.datasets,
        eval_split=with_eval,
        eval_split_max_size=config.eval_split_max_size,
        eval_split_size=config.eval_split_size,
    )

    all_samples = train_samples
    if eval_samples is not None:
        all_samples += eval_samples

    speaker_manager.set_ids_from_data(all_samples, parse_key="speaker_name")
    config.num_speakers = speaker_manager.num_speakers
    config.model_args.speakers_file = None
    config.speakers_file = None
    config.save_json(str(model_path/"config.json"))
    #print("Config.json written to " + self.MODEL_DIR + "config.json")
    config.load_json(str(model_path/"config.json"))
    #print("Config.json loaded from " + self.MODEL_DIR + "config.json")

    return TrainEvalSamples(train_samples, eval_samples)