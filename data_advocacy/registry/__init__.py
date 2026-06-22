"""Modelli dati e registry per FOIA e anagrafica enti."""

from .anagrafica import Anagrafica, Contatti, Ente
from .foia_registry import FoiaRegistry, FoiaRequest, FoiaStatus

__all__ = [
    "FoiaRequest",
    "FoiaStatus",
    "FoiaRegistry",
    "Ente",
    "Contatti",
    "Anagrafica",
]
