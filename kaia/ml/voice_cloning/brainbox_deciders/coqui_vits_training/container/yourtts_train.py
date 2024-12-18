import sys
from typing import *
from pathlib import Path
import os
import torch
from trainer import Trainer, TrainerArgs


from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits, VitsArgs, VitsAudioConfig


from dataclasses import dataclass

from stasher import Stasher
from sampler import Sampler
from drawer import Drawer
from utils import get_current_training_state
from utils_datasets import media_library_to_vctk_format, compute_speaker_encodings, process_speaker_manager


@dataclass
class TestSentence:
    text: str
    voice: str
    language: str = 'en'

class YourTTSTrain:
    def __init__(self,
                 source_media_library_path: Union[str,Path],
                 base_path: Union[str,Path],
                 pretrained_model_path: Union[str,Path],
                 sample_rate: int = 16000,
                 batch_size: int = 8,
                 max_audio_len_in_seconds: int = 8,
                 num_resample_threads: int = 10,
                 epoch_count: int = 10000,
                 with_eval: bool = True,
                 ):
        self.source_media_library = Path(source_media_library_path)
        self.AUDIO = Path(base_path)
        self.ds_name = 'data'
        self.VCTK_DOWNLOAD_PATH = str(self.AUDIO / self.ds_name)
        torch.set_num_threads(12)

        self.RESTORE_PATH = str(pretrained_model_path)
        self.SKIP_TRAIN_EPOCH = False
        self.BATCH_SIZE = batch_size
        self.SAMPLE_RATE = sample_rate
        self.MAX_AUDIO_LEN_IN_SECONDS = max_audio_len_in_seconds
        self.NUM_RESAMPLE_THREADS = num_resample_threads
        self.EPOCH_COUNT = epoch_count
        self.OUT_PATH = str(self.AUDIO / 'training_output')
        self.RUN_NAME = 'YourTTSTraining'
        self.test_sentences = [ ]
        self.MODEL_DIR = str(self.AUDIO / 'model')
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        self.with_eval = with_eval



    def _encodings(self):
        vctk_config = BaseDatasetConfig(
            formatter="vctk",
            dataset_name=self.ds_name,
            meta_file_train="",
            meta_file_val="",
            path=self.VCTK_DOWNLOAD_PATH,
            language="en",
            ignored_speakers=[]
        )

        self.DATASETS_CONFIG_LIST = [vctk_config]
        result = compute_speaker_encodings(self.DATASETS_CONFIG_LIST, self.with_eval)
        self.encodings = result


    def _configs_1(self):
        self.audio_config = VitsAudioConfig(
            sample_rate=self.SAMPLE_RATE,
            hop_length=256,
            win_length=1024,
            fft_size=1024,
            mel_fmin=0.0,
            mel_fmax=None,
            num_mels=80,
        )

        # Init VITSArgs setting the arguments that is needed for the YourTTS model
        self.model_args = VitsArgs(
            d_vector_file=self.encodings.D_VECTOR_FILES,
            use_d_vector_file=True,
            d_vector_dim=512,
            num_layers_text_encoder=10,
            speaker_encoder_model_path=self.encodings.SPEAKER_ENCODER_CHECKPOINT_PATH,
            speaker_encoder_config_path=self.encodings.SPEAKER_ENCODER_CONFIG_PATH,
            resblock_type_decoder="2",
            # On the paper, we accidentally trained the YourTTS using ResNet blocks type 2, if you like you can use the ResNet blocks type 1 like the VITS model
            # Usefull parameters to enable the Speaker Consistency Loss (SCL) discribed in the paper
            use_speaker_encoder_as_loss=True,
            # Usefull parameters to the enable multilingual training
            # use_language_embedding=True,
            # embedded_language_dim=4,
        )


    def _config_2(self):
        # General training config, here you can change the batch size and others usefull parameters
        self.config = VitsConfig(
            epochs=self.EPOCH_COUNT,
            output_path=self.OUT_PATH,
            model_args=self.model_args,
            run_name=self.RUN_NAME,
            project_name="YourTTS",
            #    run_description="""
            #            - Original YourTTS trained using VCTK dataset
            #        """,
            run_description="""YourTTS transfer learning test""",
            dashboard_logger="tensorboard",
            logger_uri=None,
            audio=self.audio_config,
            batch_size=self.BATCH_SIZE,
            batch_group_size=8,
            eval_batch_size=self.BATCH_SIZE,
            num_loader_workers=4,
            eval_split_max_size=256,
            print_step=50,
            plot_step=100,
            log_model_step=500,
            save_all_best=True,
            save_step=1000,
            save_n_checkpoints=5,
            save_checkpoints=True,
            target_loss="loss_1",
            print_eval=False,
            use_phonemes=False,
            phonemizer="espeak",
            phoneme_language="en",
            compute_input_seq_cache=True,
            add_blank=True,
            text_cleaner="multilingual_cleaners",
            phoneme_cache_path="phoneme_cache",
            precompute_num_workers=4,
            start_by_longest=True,
            datasets=self.DATASETS_CONFIG_LIST,
            cudnn_benchmark=False,
            max_audio_len=self.SAMPLE_RATE * self.MAX_AUDIO_LEN_IN_SECONDS,
            mixed_precision=False,
            test_sentences=self.test_sentences,
            # Enable the weighted sampler
            # use_weighted_sampler=True,
            use_weighted_sampler=False,
            # Ensures that all speakers are seen in the training batch equally no matter how many samples each speaker has
            weighted_sampler_attrs={"speaker_name": 1.0},
            weighted_sampler_multipliers={},
            # It defines the Speaker Consistency Loss (SCL) α to 9 like the paper
            speaker_encoder_loss_alpha=9.0,
            run_eval = self.with_eval
        )
        self.config.save_on_epoch = 10





    def _run(self):
        samples = process_speaker_manager(
            self.encodings,
            self.config,
            Path(self.VCTK_DOWNLOAD_PATH),
            Path(self.MODEL_DIR),
            self.with_eval
        )
        model = Vits.init_from_config(self.config)
        trainer = Trainer(
            TrainerArgs(restore_path=self.RESTORE_PATH, skip_train_epoch=self.SKIP_TRAIN_EPOCH),
            self.config,
            output_path=self.OUT_PATH,
            model=model,
            train_samples=samples.train_samples,
            eval_samples=samples.eval_samples,
        )
        trainer.fit()


    def make_all(self):
        path = Path(self.OUT_PATH)

        state = get_current_training_state(
            Path(self.VCTK_DOWNLOAD_PATH),
            path
        )

        if not state.has_data:
            media_library_to_vctk_format(self.source_media_library, Path(self.VCTK_DOWNLOAD_PATH), self.AUDIO/'temp', 16000)

        voices = os.listdir(Path(self.VCTK_DOWNLOAD_PATH)/'txt')

        Stasher(path).run_monitoring()
        text = "That quick beige fox jumped in the air over each thin dog. Look out, I shout, for he's foiled you again, creating chaos."
        Sampler(text, path, voices).run_monitoring()
        Drawer(path).run_monitoring()

        if not state.has_config:
            self._encodings()
            self._configs_1()
            self._config_2()
            self._run()
        else:
            state.run_continue()

