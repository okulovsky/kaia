#Not really following this one, but just for the future, if it now works
#https://colab.research.google.com/drive/1wAuG-TcZeAUYhff0f6ZiG-so9KT-sBIE?usp=sharing#scrollTo=psssJnAtRp4-
import shutil

from trainer import Trainer, TrainerArgs

from TTS.tts.configs.shared_configs import BaseDatasetConfig
from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.datasets import load_tts_samples
from TTS.tts.models.vits import Vits, VitsAudioConfig, VitsArgs
from TTS.tts.utils.text.tokenizer import TTSTokenizer
from TTS.utils.audio import AudioProcessor

from utils_datasets import media_library_to_vctk_format, compute_speaker_encodings, process_speaker_manager


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

class VITSMultispeakerTrain:
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
        self.model_path = self.base_path/'model'
        os.makedirs(self.temp_path, exist_ok=True)
        os.makedirs(self.model_path)

    def make_all(self):
        state = get_current_training_state(self.dataset_path, self.training_path)
        if not state.has_data:
            self._unpack_dataset()

        with zipfile.ZipFile(self.source_media_library_path, 'r') as zip:
            records = pickle.loads(zip.read('description.pkl'))
            voices = list(set(z['tags']['voice'] for z in records.values() if z['tags']['selected']))

        Stasher(self.training_path, 2500).run_monitoring()
        text = "That quick beige fox jumped in the air over each thin dog. Look out, I shout, for he's foiled you again, creating chaos."
        Sampler(text, self.training_path, voices).run_monitoring()
        Drawer(self.training_path).run_monitoring()

        if not state.has_config:
            self._encodings()
            self._run_training()
        else:
            state.run_continue()



    def _unpack_dataset(self):
        media_library_to_vctk_format(self.source_media_library_path, self.dataset_path, self.temp_path, 22050)


    def _encodings(self):
        vctk_config = BaseDatasetConfig(
            formatter="vctk",
            dataset_name='data',
            meta_file_train="",
            meta_file_val="",
            path=str(self.dataset_path),
            language="en",
            ignored_speakers=[]
        )

        self.DATASETS_CONFIG_LIST = [vctk_config]
        self.speaker_encodings = compute_speaker_encodings(self.DATASETS_CONFIG_LIST, True)


    def _run_training(self):
        output_path = str(self.training_path)
        SKIP_TRAIN_EPOCH = False


        audio_config = VitsAudioConfig(
            sample_rate=22050, win_length=1024, hop_length=256, num_mels=80, mel_fmin=0, mel_fmax=None
        )

        model_args = VitsArgs(
            d_vector_file=self.speaker_encodings.D_VECTOR_FILES,
            use_d_vector_file=True,
            d_vector_dim=512,
            speaker_encoder_model_path=self.speaker_encodings.SPEAKER_ENCODER_CHECKPOINT_PATH,
            speaker_encoder_config_path=self.speaker_encodings.SPEAKER_ENCODER_CONFIG_PATH,
            #num_layers_text_encoder=10
            resblock_type_decoder="2",
        )

        config = VitsConfig(
            audio=audio_config,
            run_name="vits_multispeaker",
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
            datasets=self.DATASETS_CONFIG_LIST,
            cudnn_benchmark=False,

            model_args=model_args,
        )

        # INITIALIZE THE AUDIO PROCESSOR
        # Audio processor is used for feature extraction and audio I/O.
        # It mainly serves to the dataloader and the training loggers.
        ap = AudioProcessor.init_from_config(config)

        # INITIALIZE THE TOKENIZER
        # Tokenizer is used to convert text to sequences of token IDs.
        # config is updated with the default characters if not defined in the config.
        tokenizer, config = TTSTokenizer.init_from_config(config)


        train_eval = process_speaker_manager(
            self.speaker_encodings,
            config,
            self.dataset_path,
            self.model_path,
            True
        )



        model = Vits.init_from_config(config)


        trainer = Trainer(
            TrainerArgs(restore_path=str(self.pretrained_model_path), skip_train_epoch=SKIP_TRAIN_EPOCH),
            config,
            output_path=str(self.training_path),
            model=model,
            train_samples=train_eval.train_samples,
            eval_samples=train_eval.eval_samples,
        )
        trainer.fit()





