# Código em R

Versão em **R** do pipeline de CH4 do TROPOMI/Sentinel-5P — espelha o pacote
Python `tropomi_ch4/`.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `tropomi_ch4.R` | Funções: `cdse_token()`, `ch4_series()`, `ch4_diaria()`, `ch4_mensal()`, `ch4_anual()` |
| `exemplo_series.R` | Roda as três escalas e salva CSV + figura em `data/` |
| `mapas_l2.R` | L2 cru → GeoTIFF mensal (~1 km). **Beta/avançado** |
| `gee_rgee.R` | Earth Engine no R via `rgee` (séries + rasters) |

## Requisitos

```r
install.packages(c("httr", "jsonlite", "dotenv"))   # núcleo (séries)
install.packages(c("ncdf4", "terra"))               # mapas L2 (beta)
install.packages("rgee"); rgee::ee_install()        # Earth Engine
```

## Configuração

As credenciais são lidas do arquivo **`.env`** (o mesmo do Python). Copie o
modelo e preencha:

```bash
cp .env.example .env
```

Variáveis usadas: `CDSE_CLIENT_ID`, `CDSE_CLIENT_SECRET` (séries),
`CDSE_USERNAME`, `CDSE_PASSWORD` (L2 cru) e os `CDSE_*_URL` (endpoints).

## Como rodar

Da **raiz do repositório**:

```bash
Rscript r/exemplo_series.R
```

Ou dentro do R:

```r
source("r/tropomi_ch4.R")

diaria <- ch4_diaria("2019-01-01")
mensal <- ch4_mensal("2019-01-01")
anual  <- ch4_anual("2019-01-01")
```

> Os scripts usam caminhos relativos à raiz do repositório (ex.: `source("r/...")`,
> saída em `data/`). Rode a partir da raiz.

## Observações

- `mapas_l2.R` é **beta**: baixa o granule completo, recorta ao Brasil e **apaga
  o completo** (fica só o GeoTIFF). O custo é banda/tempo (~6 GB e ~20–25 min por
  mês). Comece com `max_granules = 5`.
- O GEE (`gee_rgee.R`) depende de **cota/créditos**; sem cota, as tarefas podem
  demorar muito. Prefira um mês de teste.
