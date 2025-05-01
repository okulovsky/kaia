from dataclasses import dataclass

@dataclass
class TrainingSettings:
    language: str = 'en-us'
    sample_rate: int = 22050
    base_model: str = 'lessac.ckpt'
    batch_size: int = 8
    validation_split: float = 0.0
    max_epochs: int = 2164+6
    checkpoint_epochs: int = 1
    precision: int = 32
    num_test_examples: int = 0
    keep_intermediate: bool = False
    single_speaker_to_multi_speaker: bool = False
    continue_existing: bool = False


    
