"""Modelli dati e registry per FOIA e anagrafica enti."""

from .foia_registry import FoiaRequest, FoiaStatus, FoiaRegistry
from .anagrafica import Ente, Contatti, Anagrafica

__all__ = [
    "FoiaRequest",
    "FoiaStatus",
    "FoiaRegistry",
    "Ente",
    "Contatti",
    "Anagrafica",
]
