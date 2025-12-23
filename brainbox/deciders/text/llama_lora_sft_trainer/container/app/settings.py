from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TrainingSettings:
    """
    Settings for SFT training of LoRA adapters.

    gguf_outtype: Literal["f32", "f16", "bf16", "q8_0", "auto"]
        Output data type for GGUF conversion.
        Default is "f16".
        Recommended: use bf16 on CPU or on GPUs that support it.

    Hyperparameters Guide:
    - https://docs.unsloth.ai/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide

    Documentation:
    - https://huggingface.co/docs/transformers/en/main_classes/trainer#transformers.TrainingArguments
    - https://huggingface.co/docs/peft/en/package_reference/lora#peft.LoraConfig
    """

    hf_model_repo: str = "unsloth/gemma-3-270m-it"
    lora_config: dict[str, Any] = field(
        default_factory=lambda: {
            "r": 16,
            "lora_alpha": 32,
            "target_modules": [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
            "lora_dropout": 0.0,
            "bias": "none",
        }
    )
    training_args: dict[str, Any] = field(
        default_factory=lambda: {
            "num_train_epochs": 3.0,
            "per_device_train_batch_size": 16,
            "gradient_accumulation_steps": 1,
            "learning_rate": 2e-4,
            "logging_steps": 10,
            "save_strategy": "steps",
            "save_steps": 0.02,
            "save_total_limit": None,
            "report_to": "none",
            "weight_decay": 0.01,
            "lr_scheduler_type": "cosine",
            "warmup_ratio": 0.1,
            "seed": 252,
            "fp16": True,
        }
    )
    gguf_outtype: Literal["f32", "f16", "bf16", "q8_0", "auto"] = "f16"
