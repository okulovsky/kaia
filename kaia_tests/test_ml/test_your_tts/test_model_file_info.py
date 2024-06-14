from kaia.ml.voice_cloning.coqui_training_container.container.model_file_info import ModelFileInfo
from unittest import TestCase
from kaia.infra import Loc
import pandas as pd

class ModelFileInfoTestCase(TestCase):
    def test_parsing(self):
        array = ['best_model.pth', 'best_model_1021.pth', 'best_model_103.pth', 'best_model_1225.pth', 'best_model_1327.pth', 'best_model_1633.pth', 'best_model_62607.pth', 'best_model_63011.pth', 'best_model_73212.pth', 'best_model_7753.pth', 'stash_96341.pth', 'checkpoint_430000.pth', 'checkpoint_431000.pth', 'checkpoint_432000.pth', 'checkpoint_433000.pth', 'checkpoint_434000.pth', 'config.json', 'events.out.tfevents.1710272905.02b9cb4fe742.1.0', 'events.out.tfevents.1710318646.12814c34d4e0.120.0', 'events.out.tfevents.1710368286.f042e8454416.120.0', 'speakers.pth', 'trainer_0_log.txt', 'train_starter.py', 'train_tts.py']
        result = ModelFileInfo.parse_folder(Loc.data_folder, array)
        pd.options.display.width = None
        df = pd.DataFrame([d.__dict__ for d in result])
        df['type_index'] = df.type.apply(lambda z: z.value)
        self.assertListEqual(
            [434000, 433000, 432000, 431000, 430000, 96341, 73212, 63011, 62607, 7753, 1633, 1327, 1225, 1021, 103],
            list(df.step)
        )
        self.assertListEqual(
            [1, 1, 1, 1, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            list(df.type_index)
        )

