# TROPOMI CH4 Brasil

Tutorial e código aberto para obter e analisar a concentração de **metano (CH4)** do
satélite **Sentinel-5P (TROPOMI)** sobre o **Brasil**, em **três escalas temporais**
(diária, mensal e anual) e mapas em ~1 km.

Este repositório ensina o caminho completo: criar a conta no **Copernicus Data Space**,
gerar as credenciais, descobrir os **endpoints da API** e baixar os dados — usando a
**Statistical API** (séries) e o **L2 cru** (mapas).

> Idioma: este README e o site estão em **português** e **inglês** (`docs/pt`, `docs/en`).

[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-4a5937.svg)](LICENSE)
[![Texto: CC BY 4.0](https://img.shields.io/badge/texto-CC%20BY%204.0-b96c4c.svg)](LICENSE-docs)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-4a5937.svg)](https://www.python.org/)
[![R](https://img.shields.io/badge/R-4.x-4a5937.svg)](https://www.r-project.org/)
[![Site: Quarto](https://img.shields.io/badge/site-Quarto-b96c4c.svg)](docs/)

---

## O que você consegue aqui

| Escala | Fonte | Produto |
|---|---|---|
| Diária | Statistical API (`P1D`) | série → CSV + figura |
| Mensal | Statistical API (`P1M`) | série → CSV + figura |
| Anual | derivado do mensal | série + tendência|
| Mapas | L2 cru / Google Earth Engine | GeoTIFF ~1 km |

## Estrutura

```
tropomi-ch4-brasil/
├─ tropomi_ch4/           # pacote Python reutilizável
│  ├─ config.py           # lê credenciais do .env
│  ├─ copernicus.py       # autenticação + Statistical API
│  ├─ series.py           # séries diária / mensal / anual
│  ├─ l2.py               # L2 cru (catálogo, download, GeoTIFF)
│  └─ plot.py             # figuras padronizadas
├─ notebooks/             # uma escala por notebook
│  ├─ 01_diaria.ipynb
│  ├─ 02_mensal.ipynb
│  ├─ 03_anual.ipynb
│  ├─ 04_mapas_l2.ipynb    # L2 cru (baixa completo -> recorta -> apaga completo)
│  └─ 05_mapas_gee.ipynb   # GEE (exige cota/créditos; pode demorar meses)
├─ r/                     # versão em R (espelha o pacote Python)
│  ├─ tropomi_ch4.R        # funções de séries (P1D/P1M/anual)
│  ├─ exemplo_series.R     # roda as 3 escalas e salva CSV + figura
│  ├─ mapas_l2.R           # L2 cru -> GeoTIFF (~1 km), beta/avançado
│  └─ gee_rgee.R           # Earth Engine no R (rgee)
├─ docs/                  # site (Quarto) em PT e EN
├─ data/                  # dados de exemplo (não versionar dados grandes)
├─ requirements.txt
├─ .env.example           # modelo de credenciais
├─ CITATION.cff
├─ LICENSE                # código: MIT
└─ LICENSE-docs           # conteúdo/figuras: CC BY 4.0
```

## Início rápido

1. Crie e ative um ambiente, e instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Copie o modelo de credenciais e preencha:
   ```bash
   cp .env.example .env
   ```
3. Siga o site (`docs/`) — começando por **Conta Copernicus** e **Links da API**.
4. Rode os notebooks em `notebooks/`.

> **Nunca** suba o arquivo `.env` para o GitHub. Ele já está no `.gitignore`.

## Documentação

O tutorial completo está no site gerado com [Quarto](https://quarto.org), em `docs/`:

- `docs/pt/` — português
- `docs/en/` — inglês

Para gerar localmente:
```bash
cd docs
quarto render
```

## Citação

Se usar este material, cite:

> Beltran, L. A. (2026). *TROPOMI CH4 Brasil: tutorial e código para séries de metano
> do Sentinel-5P*. https://github.com/LudimiladeAzevedoBeltran/tropomi-ch4-brasil

Ver `CITATION.cff`.

> O arquivo `.zenodo.json` prepara o depósito no [Zenodo](https://zenodo.org).
> Ao conectar o repositório e criar uma *release*, o Zenodo gera um **DOI** citável
> (aí é só descomentar a linha `doi:` no `CITATION.cff`).

## Licença

- **Código:** MIT (ver `LICENSE`).
- **Texto e figuras:** CC BY 4.0 (ver `LICENSE-docs`).

## Autor

**Ludimila de Azevedo Beltran** — ORCID [0009-0003-5070-9472](https://orcid.org/0009-0003-5070-9472)

## Créditos dos dados

Sentinel-5P/TROPOMI — ESA / Copernicus. Dados via Copernicus Data Space Ecosystem
(Statistical API / Sentinel Hub) e Google Earth Engine.
