from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import re
import unicodedata


def normalize_name(value: str) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-zA-Z0-9]+", "", text)
    return text.lower()


@dataclass(frozen=True)
class DatasetConfig:
    key: str
    label: str
    filename_hints: List[str]
    popup_fields: List[str]
    default_color: str
    alt_color: str
    night_ops_field: str
    interdicted_field: Optional[str] = None
    interdicted_token: Optional[str] = None


DATASETS: List[DatasetConfig] = [
    DatasetConfig(
        key="privados",
        label="Aerodromos Privados",
        filename_hints=[normalize_name("AerodromosPrivados"), normalize_name("Privados")],
        popup_fields=[
            "Nome",
            "Município",
            "UF",
            "Operação Diurna",
            "Operação Noturna",
            "Superfície 1",
            "Link Portaria",
        ],
        default_color="#C46A4A",  # terracota
        alt_color="#00B6C7",  # ciano
        night_ops_field="Operação Noturna",
    ),
    DatasetConfig(
        key="publicos",
        label="Aerodromos Publicos",
        filename_hints=[normalize_name("AerodromosPublicos"), normalize_name("Publicos")],
        popup_fields=[
            "Nome",
            "Município",
            "UF",
            "Operação Diurna",
            "Operação Noturna",
            "Situação",
            "Link Portaria",
        ],
        default_color="#F4C430",  # amarelo
        alt_color="#7E57C2",  # violeta
        night_ops_field="Operação Noturna",
        interdicted_field="Situação",
        interdicted_token="Interditado",
    ),
]


def match_dataset_config(path: Path) -> Optional[DatasetConfig]:
    stem_norm = normalize_name(path.stem)
    for cfg in DATASETS:
        for hint in cfg.filename_hints:
            if hint and hint in stem_norm:
                return cfg
    return None

