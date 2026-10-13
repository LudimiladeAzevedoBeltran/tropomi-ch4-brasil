"""Figuras padronizadas para as séries de CH4."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_series(
    df: pd.DataFrame,
    title: str = "CH4 no Brasil — TROPOMI",
    ylabel: str = "CH4 (ppb)",
    outfile: str | Path | None = None,
    show: bool = True,
):
    """Plota a série (pontos/linha) com a média anual sobreposta.

    Retorna ``(fig, ax)``. Se ``outfile`` for dado, salva a figura.
    """
    d = df.dropna(subset=["ch4_ppb"]).copy()
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(d["data"], d["ch4_ppb"], color="0.6", lw=0.9, marker=".", label="Série")

    if "ano" in d.columns:
        anual = d.groupby("ano", as_index=False)["ch4_ppb"].mean()
        ax.plot(
            pd.to_datetime(anual["ano"].astype(str), format="%Y"),
            anual["ch4_ppb"],
            color="darkred", marker="o", lw=1.8, label="Média anual",
        )
        if len(anual) >= 3:
            coef = np.polyfit(anual["ano"], anual["ch4_ppb"], 1)
            ax.plot(
                pd.to_datetime(anual["ano"].astype(str), format="%Y"),
                np.polyval(coef, anual["ano"]),
                "--", color="navy", label=f"{coef[0]:.2f} ppb/ano",
            )

    ax.set_xlabel("Ano")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()

    if outfile:
        fig.savefig(outfile, dpi=150)
    if show:
        plt.show()
    return fig, ax
