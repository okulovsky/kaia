from pathlib import Path
from settings import TrainingSettings
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig
from trl import SFTTrainer
import subprocess
from functools import partial
import json
from huggingface_hub import snapshot_download


class Trainer:
    def __init__(self, adapter_name: str, guid: str) -> None:
        self.adapter_name = adapter_name
        self.guid = guid
        self.exp_folder = Path("/home/app/experiments") / self.adapter_name / self.guid
        self.settings = self._load_settings()
        self._download_model()
        self.dataset = self._load_dataset()
        self.hf_dir = self.exp_folder / "hf_checkpoints"
        self.gguf_dir = self.exp_folder / "gguf_checkpoints"
        self.hf_dir.mkdir(exist_ok=True)
        self.gguf_dir.mkdir(exist_ok=True)

    def _download_model(self) -> None:
        print(f"Loading model '{self.settings.hf_model_repo}' (will download if not in cache)...")
        snapshot_download(
            repo_id=self.settings.hf_model_repo,
        )

    def _load_settings(self) -> TrainingSettings:
        settings_path = self.exp_folder / "settings.json"
        if not settings_path.exists():
            raise FileNotFoundError(f"settings.json not found in {self.exp_folder}")

        with settings_path.open("r") as stream:
            return TrainingSettings(**json.load(stream))

    @staticmethod
    def _format_prompt(tokenizer, sample) -> str:
        inp = sample["INPUT"]
        out = sample["OUTPUT"]
        return f"{inp}{out}" + tokenizer.eos_token

    @staticmethod
    def _tokenize(
        sample, max_length, tokenizer
    ) -> (
        dict
    ):  # TODO: works for gemma3, not tested for others (padding side, tokenization differences)
        prompt = f"{sample['INPUT']}"
        prompt_len = len(tokenizer(prompt)["input_ids"])
        tokenized = tokenizer(sample["text"], padding="max_length", max_length=max_length)
        pad_len = tokenized["input_ids"].count(tokenizer.pad_token_id)
        tokenized["labels"] = tokenized["input_ids"].copy()
        tokenized["labels"][: pad_len + prompt_len] = [-100] * (pad_len + prompt_len)
        return tokenized

    def _load_dataset(self):
        tokenizer = AutoTokenizer.from_pretrained(self.settings.hf_model_repo)
        dataset = load_dataset(
            "json",
            data_files={
                "train": f"experiments/{self.adapter_name}/{self.guid}/train.jsonl",
            },
        )
        dataset["train"] = dataset["train"].map(
            lambda x: {"text": self._format_prompt(tokenizer, x)}
        )
        max_length = max(
            len(tokenizer(sample["text"])["input_ids"]) for sample in dataset["train"]
        )
        dataset["train"] = dataset["train"].map(
            partial(self._tokenize, tokenizer=tokenizer, max_length=max_length), batched=False
        )
        return dataset

    def train(self) -> None:
        model = AutoModelForCausalLM.from_pretrained(
            self.settings.hf_model_repo,
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
                        "main/convert_lora_to_gguf.py",
                        str(checkpoint),
                        "--outfile",
                        str(self.gguf_dir / f"{checkpoint.name}.gguf"),
                        "--outtype",
                        self.settings.gguf_outtype,
                    ]
                )
