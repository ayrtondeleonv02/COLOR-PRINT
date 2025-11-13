import pytest

from backend.models.parameters import PlanoParams
from backend.service.layout_service import (
    LayoutRequest,
    optimize_layout,
)


def test_layout_request_from_dict():
    data = {
        "params": {"L": 20.0, "A": 15.0, "h": 10.0},
        "tiles_x": 2,
        "tiles_y": 3,
        "medianil_x": 0.5,
        "medianil_y": 0.5,
    }
    req = LayoutRequest.from_dict(data)
    assert isinstance(req.params, PlanoParams)
    assert req.tiles_x == 2
    assert req.tiles_y == 3
    assert req.medianil_x == 0.5


def test_optimize_layout_success():
    params = PlanoParams(L=20.0, A=15.0, h=10.0)
    request = LayoutRequest(
        params=params,
        tiles_x=2,
        tiles_y=2,
        sangria_izquierda=1.0,
        sangria_derecha=1.0,
        pinza=0.5,
        contra_pinza=0.5,
    )
    response = optimize_layout(request)
    assert response.success is True
    assert response.layout is not None
    assert response.layout["planilla"] == 4
    assert response.layout["objective"] == "width"


def test_optimize_layout_invalid_tiles():
    params = PlanoParams(L=20.0, A=15.0, h=10.0)
    request = LayoutRequest(params=params, tiles_x=0, tiles_y=0)
    response = optimize_layout(request)
    assert response.success is False

