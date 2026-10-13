"""L2 cru do Sentinel-5P/TROPOMI via CDSE (mapas em ~1 km).

Fluxo (importante): para cada *granule*, o arquivo **completo** (~70 MB) é
baixado, os pixels da **região do Brasil** são acumulados, e o arquivo **completo
é EXCLUÍDO** em seguida. Só o **GeoTIFF mensal já recortado** fica salvo — por
isso o disco usado é pequeno (existe 1 granule por vez). O custo real é
banda/tempo (~6 GB e ~20-25 min por mês).

Requer as dependências opcionais: ``h5py``, ``rasterio``
(``pip install -e ".[l2]"``).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import requests

from .config import BRAZIL_BBOX, get_login
from .copernicus import get_token_password, endpoints


def _polygon(bbox: list[float]) -> str:
    x0, y0, x1, y1 = bbox
    return f"POLYGON(({x0} {y0},{x1} {y0},{x1} {y1},{x0} {y1},{x0} {y0}))"


def list_granules(year: int, month: int, bbox: list[float] | None = None) -> list[dict]:
    """Lista os *granules* L2__CH4___ que intersectam a caixa no mês."""
    bbox = bbox or BRAZIL_BBOX
    d0 = date(year, month, 1)
    d1 = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    filt = (
        "Collection/Name eq 'SENTINEL-5P' and "
        "Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and "
        "att/OData.CSC.StringAttribute/Value eq 'L2__CH4___') and "
        f"ContentDate/Start ge {d0.isoformat()}T00:00:00.000Z and "
        f"ContentDate/Start lt {d1.isoformat()}T00:00:00.000Z and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;{_polygon(bbox)}')"
    )
    out, skip = [], 0
    while True:
        r = requests.get(
            endpoints()["catalog"],
            params={
                "$filter": filt,
                "$select": "Id,Name,ContentLength",
                "$orderby": "ContentDate/Start",
                "$top": 100,
                "$skip": skip,
            },
            timeout=120,
        )
        r.raise_for_status()
        page = r.json()["value"]
        out += page
        if len(page) < 100:
            break
        skip += 100
    return out


def download(product_id: str, dest: str | Path, token: str) -> None:
    """Baixa um produto (granule) em streaming para ``dest``."""
    with requests.get(
        f"{endpoints()['download']}({product_id})/$value",
        headers={"Authorization": f"Bearer {token}"},
        stream=True,
        timeout=900,
    ) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)


def _find(h5, needle: str, suffix: str | None = None) -> str:
    found = []

    def cb(name, obj):
        import h5py

        if isinstance(obj, h5py.Dataset) and needle.lower() in name.lower():
            if suffix is None or name.lower().endswith(suffix.lower()):
                found.append(name)

    h5.visititems(cb)
    found.sort(key=len)
    return found[0]


def accumulate_granule(
    path: str | Path,
    soma: np.ndarray,
    cont: np.ndarray,
    lon_edges: np.ndarray,
    lat_edges: np.ndarray,
    min_qa: float = 0.5,
) -> int:
    """Soma CH4 e contagem do granule nas grades ``soma``/``cont``. Retorna o nº válido."""
    import h5py

    with h5py.File(path, "r") as h:
        d_ch4 = h[_find(h, "methane_mixing_ratio_bias_corrected")]
        d_qa = h[_find(h, "qa_value")]
        d_lat = h[_find(h, "latitude", "latitude")]
        d_lon = h[_find(h, "longitude", "longitude")]
        ch4 = d_ch4[()].astype("float64")
        qa = d_qa[()].astype("float64")
        lat = d_lat[()].astype("float64")
        lon = d_lon[()].astype("float64")
        fill_qa = float(np.ravel(d_qa.attrs.get("_FillValue", 255))[0])
        scale = float(np.ravel(d_qa.attrs.get("scale_factor", 1.0))[0])

    ch4, qa, lat, lon = map(np.ravel, (ch4, qa, lat, lon))
    ok = (
        (ch4 > 1000) & (ch4 < 3000) & (qa != fill_qa)
        & (np.abs(lat) <= 90) & (np.abs(lon) <= 180) & (qa * scale >= min_qa)
    )
    if ok.sum() == 0:
        return 0

    h_sum, _, _ = np.histogram2d(lon[ok], lat[ok], bins=[lon_edges, lat_edges], weights=ch4[ok])
    h_cnt, _, _ = np.histogram2d(lon[ok], lat[ok], bins=[lon_edges, lat_edges])
    soma += h_sum
    cont += h_cnt
    return int(ok.sum())


def build_monthly_geotiff(
    year: int,
    month: int,
    out_tif: str | Path,
    bbox: list[float] | None = None,
    res: float = 0.01,
    min_qa: float = 0.5,
    tmp_dir: str | Path = ".",
    max_granules: int | None = None,
) -> float:
    """Constrói o GeoTIFF mensal (~1 km) e devolve a média de CH4 (ppb)."""
    import rasterio
    from rasterio.transform import from_origin

    bbox = bbox or BRAZIL_BBOX
    out_tif = Path(out_tif)
    out_tif.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    lon_edges = np.arange(bbox[0], bbox[2] + res / 2, res)
    lat_edges = np.arange(bbox[1], bbox[3] + res / 2, res)
    soma = np.zeros((len(lon_edges) - 1, len(lat_edges) - 1))
    cont = np.zeros_like(soma)

    token = get_token_password()
    granules = list_granules(year, month, bbox)
    if max_granules:
        granules = granules[:max_granules]

    for prod in granules:
        fn = tmp_dir / prod["Name"]
        try:
            download(prod["Id"], fn, token)
            accumulate_granule(fn, soma, cont, lon_edges, lat_edges, min_qa=min_qa)
        except Exception as exc:  # renova token e tenta de novo
            print("erro:", exc, "-> renovando token")
            token = get_token_password()
            download(prod["Id"], fn, token)
            accumulate_granule(fn, soma, cont, lon_edges, lat_edges, min_qa=min_qa)
        finally:
            fn.unlink(missing_ok=True)

    media = np.where(cont > 0, soma / np.where(cont == 0, 1, cont), np.nan)
    dados = media.T[::-1, :].astype("float32")
    with rasterio.open(
        out_tif, "w", driver="GTiff", height=dados.shape[0], width=dados.shape[1],
        count=1, dtype="float32", crs="EPSG:4326",
        transform=from_origin(bbox[0], bbox[3], res, res), nodata=np.nan, compress="deflate",
    ) as dst:
        dst.write(dados, 1)
    return float(np.nanmean(media))
