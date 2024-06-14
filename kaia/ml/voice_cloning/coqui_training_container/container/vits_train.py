# https://colab.research.google.com/drive/1Swo0GH_PjjAMqYYV6He9uFaq5TQsJ7ZH?usp=sharing
import shutil

from trainer import Trainer, TrainerArgs

from TTS.tts.configs.shared_configs import BaseDatasetConfig
from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.datasets import load_tts_samples
from TTS.tts.models.vits import Vits, VitsAudioConfig
from TTS.tts.utils.text.tokenizer import TTSTokenizer
from TTS.utils.audio import AudioProcessor


from typing import *
import subprocess
from pathlib import Path
from utils import read_media_library, get_current_training_state
import os
import soundfile as sf
import zipfile
import pickle
from stasher import  Stasher
from drawer import Drawer
from sampler import Sampler

class VITSTrain:
    def __init__(self,
                 source_media_library_path: Union[str, Path],
                 base_path: Union[str, Path],
                 pretrained_model_path: Union[str, Path],
                 ):
        self.source_media_library_path = Path(source_media_library_path)
        self.base_path = Path(base_path)
        self.pretrained_model_path = pretrained_model_path


        self.dataset_path = self.base_path/'data'
        self.temp_path = self.base_path/'temp'
        self.training_path = self.base_path/'training_output'
        self.metadata_file = self.dataset_path/'metadata.csv'
        os.makedirs(self.temp_path, exist_ok=True)

    def make_all(self):
        state = get_current_training_state(self.dataset_path, self.training_path)
        if not state.has_data:
            self._unpack_dataset()

        with zipfile.ZipFile(self.source_media_library_path, 'r') as zip:
            records = pickle.loads(zip.read('description.pkl'))
            voices = list(set(z['tags']['voice'] for z in records.values()))

        Stasher(self.training_path, 2500).run_monitoring()
        text = "That quick beige fox jumped in the air over each thin dog. Look out, I shout, for he's foiled you again, creating chaos."
        Sampler(text, self.training_path, [None]).run_monitoring()
        Drawer(self.training_path).run_monitoring()

        if not state.has_config:
            self._run_training()
        else:
            state.run_continue()


    def _process_filepath(self, filepath):
        upload_dir = str(self.dataset_path)
        use_audio_filter = 'False'
        normalize_audio = 'False'

        base = os.path.basename(filepath)
        tp_s = upload_dir + "/22k_1ch/denoise/"
        tf_s = upload_dir + "/22k_1ch/denoise/" + base
        target_path = Path(tp_s)
        target_file = Path(tf_s)
        print("From: " + str(filepath))
        print("To: " + str(target_file))
        subprocess.run(["sox", "-G", "-v", "0.8", filepath, "48k.wav", "remix", "-", "rate", "48000"])
        subprocess.run(["sox", "48k.wav", "-c", "1", "-r", "48000", "-b", "16", "-e", "signed-integer", "-t", "raw", "rnn.raw"])  # convert wav to raw
        # subprocess.run(["/content/rnnoise/examples/rnnoise_demo", "temp.raw", "rnn.raw"]) # apply rnnoise
        subprocess.run(["sox", "-G", "-v", "0.8", "-r", "48k", "-b", "16", "-e", "signed-integer", "rnn.raw", "-t", "wav", "rnn.wav"])  # convert raw back to wav
        subprocess.run(["mkdir", "-p", str(target_path)])
        if use_audio_filter == "True":
            print("Running filter...")
            subprocess.run(
                ["sox", "rnn.wav", str(target_file), "remix", "-", "highpass", "50", "lowpass", "8000", "rate",
                 "22050"])  # apply high/low pass filter and change sr to 22050Hz
            data, rate = sf.read(target_file)
        elif use_audio_filter == "False":
            print("Skipping filter...")
            subprocess.run(["sox", "rnn.wav", str(target_file), "remix", "-", "rate",
                            "22050"])  # apply high/low pass filter and change sr to 22050Hz
            data, rate = sf.read(target_file)
            # peak normalize audio to -6 dB
        if normalize_audio == "True":
            import pyloudnorm as pyln #let's try without it because I don't want to update container dependencies
            print("Output normalized")
            peak_normalized_audio = pyln.normalize.peak(data, -6.0)

            # measure the loudness first
            meter = pyln.Meter(rate)  # create BS.1770 meter
            loudness = meter.integrated_loudness(data)

            # loudness normalize audio to -25 dB LUFS
            loudness_normalized_audio = pyln.normalize.loudness(data, loudness, -25.0)
            sf.write(target_file, data=loudness_normalized_audio, samplerate=22050)
            print("")
        if normalize_audio == "False":
            print("File written without normalizing")
            sf.write(target_file, data=data, samplerate=22050)
            print("")

    def _unpack_dataset(self):
        os.makedirs(self.dataset_path, exist_ok=True)
        os.makedirs(self.training_path, exist_ok=True)
        wavs = self.dataset_path/'wavs'
        os.makedirs(wavs, exist_ok=True)
        with open(self.metadata_file, 'w', encoding='utf-8') as outfile:
            for record in read_media_library(self.source_media_library_path):
                filepath = self.temp_path/(record.filename+'.wav')
                with open(filepath, 'wb') as file:
                    file.write(record.content)
                self._process_filepath(filepath)
                os.unlink(filepath)

                shutil.move(self.dataset_path/f'22k_1ch/denoise/{record.filename}.wav', wavs/f'{record.filename}.wav')

                outfile.write(record.filename + '|' + record.text + '|' + record.text + '\n')


    def _run_training(self):
        output_path = str(self.training_path)
        SKIP_TRAIN_EPOCH = False
        dataset_config = BaseDatasetConfig(
            formatter="ljspeech",
            meta_file_train=str(self.metadata_file),
            path=str(self.dataset_path)
        )
        audio_config = VitsAudioConfig(
            sample_rate=22050, win_length=1024, hop_length=256, num_mels=80, mel_fmin=0, mel_fmax=None
        )

        config = VitsConfig(
            audio=audio_config,
            run_name="vits_ljspeech",
            batch_size=16,
            eval_batch_size=16,
            batch_group_size=16,
            #    num_loader_workers=8,
            num_loader_workers=2,
            num_eval_loader_workers=2,
            run_eval=True,
            test_delay_epochs=-1,
            epochs=100000,
            save_step=1000,
            save_all_best=True,
            save_checkpoints=True,
            save_n_checkpoints=4,
            save_best_after=1000,
            text_cleaner="english_cleaners",
            #text_cleaner="multilingual_cleaners",
            use_phonemes=True,
            phoneme_language="en-us",
            phoneme_cache_path=os.path.join(output_path, "phoneme_cache"),
            compute_input_seq_cache=True,
            print_step=25,
            print_eval=True,
            mixed_precision=True,
            output_path=output_path,
            datasets=[dataset_config],
            cudnn_benchmark=False,
        )

        # INITIALIZE THE AUDIO PROCESSOR
        # Audio processor is used for feature extraction and audio I/O.
        # It mainly serves to the dataloader and the training loggers.
        ap = AudioProcessor.init_from_config(config)

        # INITIALIZE THE TOKENIZER
        # Tokenizer is used to convert text to sequences of token IDs.
        # config is updated with the default characters if not defined in the config.
        tokenizer, config = TTSTokenizer.init_from_config(config)

        # LOAD DATA SAMPLES
        # Each sample is a list of ```[text, audio_file_path, speaker_name]```
        # You can define your custom sample loader returning the list of samples.
        # Or define your custom formatter and pass it to the `load_tts_samples`.
        # Check `TTS.tts.datasets.load_tts_samples` for more details.
        train_samples, eval_samples = load_tts_samples(
            dataset_config,
            eval_split=True,
            eval_split_max_size=config.eval_split_max_size,
            eval_split_size=config.eval_split_size,
        )

        model = Vits.init_from_config(config)

        CONTINUE_PATH = str(self.pretrained_model_path)

        trainer = Trainer(
            TrainerArgs(restore_path=CONTINUE_PATH, skip_train_epoch=SKIP_TRAIN_EPOCH),
            config,
            output_path=CONTINUE_PATH, #TODO: this is wrong
            model=model,
            train_samples=train_samples,
            eval_samples=eval_samples,
        )
        trainer.fit()





