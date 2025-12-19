from pathlib import Path
from settings import TrainingSettings
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig
from trl import SFTTrainer
import subprocess
from functools import partial
import json


class Trainer:
    def __init__(self, exp_folder: str) -> None:
        self.exp_folder = Path(exp_folder)
        self.settings = self._load_settings()
        self.dataset = self._load_dataset()
        self.tokenizer = AutoTokenizer.from_pretrained(self.settings.model_name)
        self.hf_dir = self.exp_folder / "hf_checkpoints"
        self.gguf_dir = self.exp_folder / "gguf_checkpoints"
        self.hf_dir.mkdir(exist_ok=True)
        self.gguf_dir.mkdir(exist_ok=True)

    def _load_settings(self) -> TrainingSettings:
        settings_path = self.exp_folder / "settings.json"
        if not settings_path.exists():
            raise FileNotFoundError(f"settings.json not found in {self.exp_folder}")

        with settings_path.open("r") as stream:
            return TrainingSettings(**json.load(stream))

    def _format_prompt(self, sample) -> str:
        inp = sample["INPUT"]
        out = sample["OUTPUT"]
        return f"{inp}{out}" + self.tokenizer.eos_token

    def _tokenize(
        self, sample, max_length
    ) -> (
        dict
    ):  # TODO: works for gemma3, not tested for others (padding side, tokenization differences)
        prompt = f"{sample['INPUT']}"
        prompt_len = len(self.tokenizer(prompt)["input_ids"])
        tokenized = self.tokenizer(sample["text"], padding="max_length", max_length=max_length)
        pad_len = tokenized["input_ids"].count(self.tokenizer.pad_token_id)
        tokenized["labels"] = tokenized["input_ids"].copy()
        tokenized["labels"][: pad_len + prompt_len] = [-100] * (pad_len + prompt_len)
        return tokenized

    def _load_dataset(self):
        dataset = load_dataset(
            "json",
            data_files={
                "train": self.exp_folder / "train.jsonl",
            },
        )
        dataset["train"] = dataset["train"].map(lambda x: {"text": self._format_prompt(x)})
        max_length = max(
            len(self.tokenizer(sample["text"])["input_ids"]) for sample in dataset["train"]
        )
        dataset["train"] = dataset["train"].map(
            partial(self._tokenize, max_length=max_length), batched=False
        )
        return dataset

    def train(self) -> None:
        model = AutoModelForCausalLM.from_pretrained(
            self.settings.model_name,
            device_map="auto",
            use_cache=False,
            attn_implementation="eager",
        )
        peft_config = LoraConfig(**self.settings.lora_config)
        training_args = TrainingArguments(output_dir=self.hf_dir, **self.settings.training_args)
        trainer = SFTTrainer(
            model=model,
            train_dataset=self.dataset["train"],
            peft_config=peft_config,
            args=training_args,
        )

        trainer.train()

    def convert_lora_to_gguf(self) -> None:
        for checkpoint in self.hf_dir.iterdir():
            if checkpoint.is_dir() and checkpoint.name.startswith("checkpoint-"):
                subprocess.run(
                    [
                        "python3",
                        "convert_lora_to_gguf.py",
                        str(checkpoint),
                        "--outfile",
                        str(self.gguf_dir / f"{checkpoint.name}.gguf"),
                        "--outtype",
                        self.settings.gguf_outtype,
                    ]
                )
