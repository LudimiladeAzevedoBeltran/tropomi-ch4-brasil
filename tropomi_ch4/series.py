"""Séries temporais de CH4 sobre o Brasil (diária, mensal e anual).

Todas usam a Statistical API (ver :mod:`tropomi_ch4.copernicus`). A escala
anual é derivada da mensal — mais robusta do que depender de ``P1Y`` na API.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from .config import BRAZIL_BBOX
from .copernicus import get_token_client, statistical_series


def _standardize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ano"] = df["data"].dt.year
    df["mes"] = df["data"].dt.month
    return df.sort_values("data").reset_index(drop=True)


def daily(
    start: str = "2019-01-01",
    end: str | None = None,
    bbox: list[float] | None = None,
    res: float = 0.1,
) -> pd.DataFrame:
    """Série **diária** (``P1D``). Faz uma requisição por ano (mais robusto)."""
    return _by_year("P1D", start, end, bbox or BRAZIL_BBOX, res)


def monthly(
    start: str = "2019-01-01",
    end: str | None = None,
    bbox: list[float] | None = None,
    res: float = 0.1,
) -> pd.DataFrame:
    """Série **mensal** (``P1M``) em uma única requisição."""
    bbox = bbox or BRAZIL_BBOX
    token = get_token_client()
    df = statistical_series("P1M", start, end, bbox=bbox, res=res, token=token)
    return _standardize(df)


def annual(
    start: str = "2019-01-01",
    end: str | None = None,
    bbox: list[float] | None = None,
    res: float = 0.1,
) -> pd.DataFrame:
    """Série **anual** (média dos meses válidos de cada ano)."""
    df = monthly(start=start, end=end, bbox=bbox, res=res)
    grouped = (
        df.dropna(subset=["ch4_ppb"])
        .groupby("ano", as_index=False)
        .agg(ch4_ppb=("ch4_ppb", "mean"), n_validos=("n_validos", "sum"))
    )
    grouped["data"] = pd.to_datetime(grouped["ano"].astype(str), format="%Y")
    return grouped[["data", "ano", "ch4_ppb", "n_validos"]]


def _by_year(
    interval: str,
    start: str,
    end: str | None,
    bbox: list[float],
    res: float,
) -> pd.DataFrame:
    token = get_token_client()
    inicio = pd.Timestamp(start)
    fim = pd.Timestamp(end) if end else pd.Timestamp(date.today())
    partes = []
    for ano in range(inicio.year, fim.year + 1):
        f0 = max(inicio, pd.Timestamp(f"{ano}-01-01")).strftime("%Y-%m-%d")
        f1 = min(fim, pd.Timestamp(f"{ano}-12-31")).strftime("%Y-%m-%d")
        partes.append(statistical_series(interval, f0, f1, bbox=bbox, res=res, token=token))
    return _standardize(pd.concat(partes, ignore_index=True))
