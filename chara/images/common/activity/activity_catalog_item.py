from dataclasses import dataclass, field
from pathlib import Path
import yaml
from foundation_kaia.marshalling import Serializer
from .fingerprint import ImageSetupFingerprint


@dataclass
class ActivityCatalogItem:
    fingerprint: ImageSetupFingerprint
    activities: list[str] = field(default_factory=list)

    @staticmethod
    def read_catalog(path: Path) -> dict[ImageSetupFingerprint, 'ActivityCatalogItem']:
        if not path.exists():
            return {}
        with open(path) as f:
            raw = yaml.safe_load(f)
        if not raw:
            return {}
        items: list[ActivityCatalogItem] = _SERIALIZER.from_json(raw)
        return {item.fingerprint: item for item in items}

    @staticmethod
    def write_catalog(path: Path, catalog: dict[ImageSetupFingerprint, 'ActivityCatalogItem']) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.safe_dump(_SERIALIZER.to_json(list(catalog.values())), f, allow_unicode=True, sort_keys=False)


_SERIALIZER = Serializer.parse(list[ActivityCatalogItem])
