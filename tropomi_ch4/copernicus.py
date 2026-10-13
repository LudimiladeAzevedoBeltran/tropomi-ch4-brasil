"""Acesso à API do Copernicus Data Space (Sentinel Hub).

Contém a autenticação (OAuth client e login de conta) e a consulta à
**Statistical API**, que devolve estatísticas agregadas (ex.: média) de CH4
sobre uma área, sem baixar imagens.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import requests

from .config import BRAZIL_BBOX, Credentials, endpoints, get_credentials, get_login

# Evalscript: lê a banda CH4 (com filtro de qualidade minQa=50) e devolve a média.
EVALSCRIPT = (
    '//VERSION=3\n'
    'function setup(){return{input:[{bands:["CH4","dataMask"],minQa:50}],'
    'output:[{id:"data",bands:1},{id:"dataMask",bands:1}]};}\n'
    'function evaluatePixel(s){return{data:[s.CH4],dataMask:[s.dataMask]};}'
)


def get_token_client(creds: Credentials | None = None) -> str:
    """Token via ``client_credentials`` (OAuth client). Usado pelas séries."""
    creds = creds or get_credentials()
    url = endpoints()["token"]
    r = requests.post(
        url,
        data={
            "grant_type": "client_credentials",
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Falha no login ({r.status_code}): {r.text[:300]}")
    return r.json()["access_token"]


def get_token_password(creds: Credentials | None = None) -> str:
    """Token via ``password`` (login da conta). Usado no download do L2 cru."""
    creds = creds or get_login()
    url = endpoints()["token"]
    r = requests.post(
        url,
        data={
            "grant_type": "password",
            "client_id": "cdse-public",
            "username": creds.username,
            "password": creds.password,
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Falha no login ({r.status_code}): {r.text[:300]}")
    return r.json()["access_token"]


def statistical_series(
    interval: str,
    start: str,
    end: str | None = None,
    bbox: list[float] | None = None,
    res: float = 0.1,
    token: str | None = None,
) -> pd.DataFrame:
    """Consulta a Statistical API e devolve uma série temporal de CH4.

    Parâmetros
    ----------
    interval:
        Periodicidade no formato ISO 8601 aceito pela API. Use ``"P1D"`` para
        diária e ``"P1M"`` para mensal.
    start, end:
        Datas no formato ``"AAAA-MM-DD"``. ``end=None`` usa o mês corrente.
    bbox:
        Caixa ``[lon_min, lat_min, lon_max, lat_max]``. Padrão: Brasil.
    res:
        Resolução da agregação no servidor, em graus.
    token:
        Token já obtido (evita novo login). Se ``None``, autentica via OAuth client.

    Retorna
    -------
    ``pandas.DataFrame`` com colunas ``data``, ``ch4_ppb`` e ``n_validos``.
    """
    bbox = bbox or BRAZIL_BBOX
    token = token or get_token_client()
    f0 = f"{start}T00:00:00Z"
    f1 = f"{end or date.today().replace(day=1).isoformat()}T00:00:00Z"

    body = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
            },
            "data": [
                {
                    "type": "sentinel-5p-l2",
                    "dataFilter": {"timeRange": {"from": f0, "to": f1}},
                }
            ],
        },
        "aggregation": {
            "timeRange": {"from": f0, "to": f1},
            "aggregationInterval": {"of": interval},
            "evalscript": EVALSCRIPT,
            "resx": res,
            "resy": res,
        },
        "calculations": {"default": {"statistics": {"default": {}}}},
    }

    r = requests.post(
        endpoints()["statistics"],
        json=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=900,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Erro {r.status_code}: {r.text[:300]}")

    linhas = []
    for item in r.json()["data"]:
        st = item["outputs"]["data"]["bands"]["B0"]["stats"]
        linhas.append(
            {
                "data": item["interval"]["from"][:10],
                "ch4_ppb": st["mean"],
                "n_validos": st["sampleCount"] - st["noDataCount"],
            }
        )

    df = pd.DataFrame(linhas)
    df["data"] = pd.to_datetime(df["data"])
    df["ch4_ppb"] = pd.to_numeric(df["ch4_ppb"], errors="coerce")
    return df
