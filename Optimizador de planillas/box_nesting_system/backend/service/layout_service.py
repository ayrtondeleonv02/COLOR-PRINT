"""
Service-layer helpers that expose backend layout calculations
in a UI-agnostic, serializable format.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import logging

from backend.models.parameters import PlanoParams
from backend.nesting.engine import NestingEngine


logger = logging.getLogger(__name__)


@dataclass
class LayoutRequest:
    """Serializable request payload for simple layout summaries."""

    params: PlanoParams
    tiles_x: int = 1
    tiles_y: int = 1
    medianil_x: float = 0.0
    medianil_y: float = 0.0
    paso_y: float = 0.5
    paso_x: float = 0.1
    clearance_cm: float = 0.0
    sangria_izquierda: float = 0.0
    sangria_derecha: float = 0.0
    pinza: float = 0.0
    contra_pinza: float = 0.0
    objective: str = "width"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayoutRequest":
        params_data = data.get("params", {})
        params = params_data if isinstance(params_data, PlanoParams) else PlanoParams.from_dict(params_data)
        return cls(
            params=params,
            tiles_x=data.get("tiles_x", 1),
            tiles_y=data.get("tiles_y", 1),
            medianil_x=data.get("medianil_x", 0.0),
            medianil_y=data.get("medianil_y", 0.0),
            paso_y=data.get("paso_y", 0.5),
            paso_x=data.get("paso_x", 0.1),
            clearance_cm=data.get("clearance_cm", 0.0),
            sangria_izquierda=data.get("sangria_izquierda", 0.0),
            sangria_derecha=data.get("sangria_derecha", 0.0),
            pinza=data.get("pinza", 0.0),
            contra_pinza=data.get("contra_pinza", 0.0),
            objective=data.get("objective", "width"),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["params"] = self.params.to_dict()
        return payload


@dataclass
class LayoutResponse:
    """Serializable response payload."""

    success: bool
    layout: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "layout": self.layout,
            "message": self.message,
        }


def optimize_layout(request: LayoutRequest) -> LayoutResponse:
    """
    Compute a lightweight layout summary without touching the UI layer.

    This helper is intentionally pure so it can back future HTTP/CLI interfaces.
    """
    try:
        if request.tiles_x <= 0 or request.tiles_y <= 0:
            return LayoutResponse(False, message="La cantidad de tiles debe ser mayor a 0 en ambos ejes.")

        engine = NestingEngine(request.params)
        bbox = engine.calculate_global_bbox(
            request.tiles_x,
            request.tiles_y,
            request.medianil_x,
            request.medianil_y,
            request.objective,
        )
        if not bbox:
            return LayoutResponse(False, message="No se pudo calcular el bounding box para el layout solicitado.")

        medida_x = bbox[2] - bbox[0]
        medida_y = bbox[3] - bbox[1]

        medida_x_total = medida_x + request.sangria_izquierda + request.sangria_derecha
        medida_y_total = medida_y + request.pinza + request.contra_pinza

        layout_summary = {
            "tiles_x": request.tiles_x,
            "tiles_y": request.tiles_y,
            "planilla": request.tiles_x * request.tiles_y,
            "medida_x_cm": round(medida_x_total, 2),
            "medida_y_cm": round(medida_y_total, 2),
            "area_cm2": round(medida_x_total * medida_y_total, 2),
            "objective": request.objective,
        }
        return LayoutResponse(True, layout_summary)

    except Exception as exc:
        logger.error("Layout service failed: %s", exc, exc_info=True)
        return LayoutResponse(False, message=str(exc))
