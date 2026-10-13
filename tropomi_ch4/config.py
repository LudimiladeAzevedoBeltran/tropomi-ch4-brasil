"""Configuração e credenciais.

As credenciais são lidas do arquivo `.env` (ou de variáveis de ambiente).
Copie `.env.example` para `.env` e preencha. O `.env` nunca deve ir para o Git.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv é opcional na importação
    pass


# Caixa (bounding box) aproximada do Brasil: [lon_min, lat_min, lon_max, lat_max]
BRAZIL_BBOX: list[float] = [-74.0, -34.0, -34.0, 6.0]

# Endpoints padrão da API Copernicus (CDSE / Sentinel Hub).
DEFAULT_ENDPOINTS = {
    "token": "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
    "statistics": "https://sh.dataspace.copernicus.eu/api/v1/statistics",
    "catalog": "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
    "download": "https://download.dataspace.copernicus.eu/odata/v1/Products",
}

_PLACEHOLDERS = {"", "COLE_SEU_CLIENT_ID", "COLE_SEU_CLIENT_SECRET", "SUA_SENHA"}


@dataclass(frozen=True)
class Credentials:
    """Credenciais da conta CDSE.

    - ``client_id`` / ``client_secret``: OAuth client (Statistical API).
    - ``username`` / ``password``: login normal da conta (download do L2 cru).
    """

    client_id: str
    client_secret: str
    username: str
    password: str

    @property
    def has_oauth(self) -> bool:
        return bool(self.client_id and self.client_secret
                    and self.client_id not in _PLACEHOLDERS
                    and self.client_secret not in _PLACEHOLDERS)

    @property
    def has_login(self) -> bool:
        return bool(self.username and self.password and self.password not in _PLACEHOLDERS)


def get_credentials() -> Credentials:
    """Lê as credenciais do ambiente e valida o essencial.

    Levanta ``RuntimeError`` se faltar o OAuth client (usado pelas séries).
    O login (e-mail/senha) só é exigido pela função que baixa o L2 cru.
    """
    creds = Credentials(
        client_id=os.getenv("CDSE_CLIENT_ID", ""),
        client_secret=os.getenv("CDSE_CLIENT_SECRET", ""),
        username=os.getenv("CDSE_USERNAME", ""),
        password=os.getenv("CDSE_PASSWORD", ""),
    )
    if not creds.has_oauth:
        raise RuntimeError(
            "OAuth client ausente. Defina CDSE_CLIENT_ID e CDSE_CLIENT_SECRET no .env "
            "(veja .env.example)."
        )
    return creds


def get_login() -> Credentials:
    """Como :func:`get_credentials`, mas exige também o login (e-mail/senha)."""
    creds = get_credentials()
    if not creds.has_login:
        raise RuntimeError(
            "Login da conta ausente. Defina CDSE_USERNAME e CDSE_PASSWORD no .env."
        )
    return creds


def endpoints() -> dict[str, str]:
    """Endpoints da API, permitindo sobrescrever via variáveis de ambiente."""
    return {
        "token": os.getenv("CDSE_TOKEN_URL", DEFAULT_ENDPOINTS["token"]),
        "statistics": os.getenv("CDSE_STATS_URL", DEFAULT_ENDPOINTS["statistics"]),
        "catalog": os.getenv("CDSE_CATALOG_URL", DEFAULT_ENDPOINTS["catalog"]),
        "download": os.getenv("CDSE_DOWNLOAD_URL", DEFAULT_ENDPOINTS["download"]),
    }


def output_dir() -> Path:
    """Pasta base de saída (``OUTPUT_DIR`` no ambiente; padrão: pasta atual)."""
    return Path(os.getenv("OUTPUT_DIR") or ".").resolve()
