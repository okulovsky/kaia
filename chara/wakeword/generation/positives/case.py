from ..dto import AudioCase
from .voice_description_generator import VoiceDescriptionGenerator


def create_case(settings, group, attempt):
    class_label, split = group.rsplit("_", 1)
    variant = settings.target_variants[attempt["seed"] % len(settings.target_variants)]
    return AudioCase(
        sample_id=attempt["sample_id"],
        lineage_id=attempt["sample_id"],
        class_label=class_label,
        split=split,
        seed=attempt["seed"],
        attempt_index=attempt.get("index", 0),
        text=variant,
        voice_description=VoiceDescriptionGenerator().describe(attempt["seed"]),
        task_ids={"voiceover": attempt["task_id"]},
    )
