import torch
import os
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS, Conditionals  # Добавь импорт Conditionals

class Model:
    def __init__(self, device='cuda'):
        self.model = ChatterboxMultilingualTTS.from_pretrained(device=device)
        self.device = device  # Сохраним для удобства

    def compute_embedding(self, src_path):
        self.model.prepare_conditionals(src_path, exaggeration=0.5)
        return self.model.conds  # Теперь возвращаем Conditionals, а не модель

    def voiceover(self, text, conds, language, output_file, exaggeration=0.5, cfg_weight=1):
        self.model.conds = conds  # Устанавливаем кондишены для этого спикера
        # Если exaggeration отличается, generate сам обновит его в conds.t3.emotion_adv
        wav_out = self.model.generate(
            text=text,
            language_id=language,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight
        )
        ta.save(output_file, wav_out, self.model.sr)

        print(os.listdir("/home/app/main"), "================================================================================================================================")