from dataclasses import dataclass

@dataclass
class TrainingSettings:
    language = 'en-us'
    sample_rate = 22050
    base_model = 'lessac.ckpt'
    batch_size: int = 8
    validation_split: float = 0.0
    max_epochs: int = 2170
    checkpoint_epochs: int = 1
    precision: int = 32
    num_test_examples: int = 0
    keep_intermediate: bool = False

    
