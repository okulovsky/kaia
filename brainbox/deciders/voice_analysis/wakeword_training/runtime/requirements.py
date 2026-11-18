"""Expected dataset constraints are independent of received metadata."""

from .io import read_json
from .manifests import normalized


def requirements_from_config(path):
    config = read_json(path)
    generation = config.get("generation", {})
    training = config.get("training", config)
    variants = training.get(
        "expected_target_variants", generation.get("target_variants")
    )
    normalized(variants)
    minimum = training.get("minimum_positive_counts")
    if minimum is None:
        counts = generation.get("counts", {})
        minimum = {
            "train": counts.get("positive_train"),
            "validation": counts.get("positive_test"),
        }
    if set(minimum) != {"train", "validation"} or any(
        type(v) is not int or v <= 0 for v in minimum.values()
    ):
        raise ValueError("explicit positive train/validation minimum counts required")
    return {
        "target_variants": variants,
        "minimum_positive_counts": minimum,
        "resource_profile": training.get("server_resource_profile", "acav-notebook-v1"),
    }
