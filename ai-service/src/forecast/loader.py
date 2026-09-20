"""Modul loader singleton untuk memuat model champion yang telah dilatih."""

from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging
import joblib

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "champion_model.joblib"
METADATA_PATH = ARTIFACTS_DIR / "metadata.json"

_cached_model: Optional[Any] = None
_cached_metadata: Optional[Dict[str, Any]] = None


def is_champion_model_available() -> bool:
    """Mengecek apakah file model champion (.joblib) tersedia di direktori artifacts."""
    return MODEL_PATH.exists() and MODEL_PATH.is_file()


def get_champion_model(force_reload: bool = False) -> Optional[Any]:
    """
    Memuat model champion ke memori (singleton cache).
    Mengembalikan None jika file belum tersedia.
    """
    global _cached_model
    if _cached_model is not None and not force_reload:
        return _cached_model

    if not is_champion_model_available():
        logger.info("Champion model belum tersedia di %s. Menggunakan baseline fallback.", MODEL_PATH)
        return None

    try:
        _cached_model = joblib.load(MODEL_PATH)
        logger.info("Berhasil memuat champion model dari %s", MODEL_PATH)
        return _cached_model
    except Exception as exc:
        logger.warning("Gagal memuat champion model dari %s: %s", MODEL_PATH, exc)
        return None


def get_model_metadata() -> Dict[str, Any]:
    """Membaca metadata arsitektur, metrik, dan parameter model champion."""
    global _cached_metadata
    if _cached_metadata is not None:
        return _cached_metadata

    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                _cached_metadata = json.load(f)
                return _cached_metadata
        except Exception as exc:
            logger.warning("Gagal membaca metadata model: %s", exc)

    return {
        "model_name": "unknown",
        "description": "Model metadata tidak tersedia",
        "metrics": {},
    }
