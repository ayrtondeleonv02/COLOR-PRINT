"""
Box template definitions for preset proportions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from .parameters import PlanoParams


@dataclass(frozen=True)
class TemplateDefinition:
    name: str
    builder: Callable[[PlanoParams], Dict[str, List[float]]]


def _template_fondo_automatico(p: PlanoParams) -> Dict[str, List[float]]:
    L, A, ceja = p.L, p.A, p.cIzq
    return {
        "Tapas": [0.0, A / 2.0, A, A / 2.0],
        "CejaSup": [0.0, 0.0, ceja, 0.0],
        "Bases": [A/1.5, L / 3.0, A/1.5, L / 3.0],
        "CejaInf": [0.0, 0.0, 0.0, 0.0],
    }


def _template_francesa(p: PlanoParams) -> Dict[str, List[float]]:
    L, A, ceja = p.L, p.A, p.cIzq
    return {
        "Tapas": [0.0, A / 2.0, A, A / 2.0],
        "CejaSup": [0.0, 0.0, ceja, 0.0],
        "Bases": [A, A / 2.0, 0.0, A / 2.0],
        "CejaInf": [ceja, 0.0, 0.0, 0.0],
    }


def _template_avion(p: PlanoParams) -> Dict[str, List[float]]:
    L, A, ceja = p.L, p.A, p.cIzq
    return {
        "Tapas": [A, A / 2.0, 0.0, A / 2.0],
        "CejaSup": [ceja, 0.0, 0.0, 0.0],
        "Bases": [A, A / 2.0, 0.0, A / 2.0],
        "CejaInf": [ceja, 0.0, 0.0, 0.0],
    }


TEMPLATES: Dict[str, TemplateDefinition] = {
    "personalizado": TemplateDefinition("personalizado", lambda p: {}),
    "fondo automatico": TemplateDefinition("fondo automatico", _template_fondo_automatico),
    "avion": TemplateDefinition("avion", _template_avion),
    "francesa": TemplateDefinition("francesa", _template_francesa),
}


def get_template(name: str | None) -> TemplateDefinition:
    key = (name or "personalizado").strip().lower()
    return TEMPLATES.get(key, TEMPLATES["personalizado"])
