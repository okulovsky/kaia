import torch
import soundfile as sf
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer, set_seed


class Model:
    def __init__(self, repository: str):
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.model = ParlerTTSForConditionalGeneration.from_pretrained(repository).to(self.device)
        self.model.eval()
        self.tokenizer = AutoTokenizer.from_pretrained(repository)
        self.description_tokenizer = AutoTokenizer.from_pretrained(self.model.config.text_encoder._name_or_path)
        self.sampling_rate = self.model.config.sampling_rate

    def voiceover(self, text, description, output_file, temperature=1.0, seed=None):
        if seed is not None:
            set_seed(seed)
        description_input = self.description_tokenizer(description, return_tensors='pt').to(self.device)
        prompt_input = self.tokenizer(text, return_tensors='pt').to(self.device)
        with torch.no_grad():
            generation = self.model.generate(
                input_ids=description_input.input_ids,
                attention_mask=description_input.attention_mask,
                prompt_input_ids=prompt_input.input_ids,
                prompt_attention_mask=prompt_input.attention_mask,
                do_sample=True,
                temperature=temperature,
            )
        audio = generation.cpu().numpy().squeeze()
        sf.write(output_file, audio, self.sampling_rate)
