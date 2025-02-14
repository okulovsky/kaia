from dataclasses import dataclass

@dataclass
class TrainingSettings:
    language = 'en-us'
    sample_rate = 22050
    base_model = 'lessac.ckpt'
    
