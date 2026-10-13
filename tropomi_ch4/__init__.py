"""tropomi_ch4 — séries e mapas de metano (CH4) do Sentinel-5P/TROPOMI para o Brasil."""

from __future__ import annotations

from . import config, copernicus, plot, series
from .config import BRAZIL_BBOX, get_credentials, get_login
from .copernicus import get_token_client, get_token_password, statistical_series
from .series import annual, daily, monthly

# ``l2`` depende de h5py/rasterio (opcionais) e é importado sob demanda:
#   from tropomi_ch4 import l2

__version__ = "0.1.0"

__all__ = [
    "config",
    "copernicus",
    "series",
    "plot",
    "BRAZIL_BBOX",
    "get_credentials",
    "get_login",
    "get_token_client",
    "get_token_password",
    "statistical_series",
    "daily",
    "monthly",
    "annual",
    "__version__",
]
