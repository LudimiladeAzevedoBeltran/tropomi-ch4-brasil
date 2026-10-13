# ===========================================================================
# tropomi_ch4 (R) — séries de CH4 do TROPOMI/Sentinel-5P via API do Copernicus
#
# Espelha o pacote Python `tropomi_ch4`. Lê as credenciais do arquivo `.env`.
#
# Uso:
#   source("r/tropomi_ch4.R")
#   df <- ch4_mensal("2019-01-01")
#
# Pacotes: httr, jsonlite (+ dotenv, opcional, para ler o .env)
# ===========================================================================

suppressPackageStartupMessages({
  library(httr)
  library(jsonlite)
})
if (requireNamespace("dotenv", quietly = TRUE)) dotenv::load_dot_env()

`%||%` <- function(a, b) if (is.null(a)) b else a

# Caixa (bounding box) do Brasil: [lon_min, lat_min, lon_max, lat_max]
brazil_bbox <- c(-74, -34, -34, 6)

.ch4_evalscript <- paste0(
  "//VERSION=3\n",
  "function setup(){return{input:[{bands:[\"CH4\",\"dataMask\"],minQa:50}],",
  "output:[{id:\"data\",bands:1},{id:\"dataMask\",bands:1}]};}\n",
  "function evaluatePixel(s){return{data:[s.CH4],dataMask:[s.dataMask]};}"
)

# --- Autenticação (OAuth client) -------------------------------------------
cdse_token <- function() {
  r <- POST(
    Sys.getenv("CDSE_TOKEN_URL"),
    body = list(
      grant_type = "client_credentials",
      client_id = Sys.getenv("CDSE_CLIENT_ID"),
      client_secret = Sys.getenv("CDSE_CLIENT_SECRET")
    ),
    encode = "form"
  )
  if (status_code(r) != 200) {
    stop("Falha no login (", status_code(r), "): ",
         content(r, "text", encoding = "UTF-8"))
  }
  content(r, as = "parsed")$access_token
}

# --- Série temporal de CH4 (Statistical API) -------------------------------
ch4_series <- function(interval = "P1D", from, to = NULL,
                       bbox = brazil_bbox, res = 0.1, token = NULL) {
  if (is.null(to)) to <- format(Sys.Date(), "%Y-%m-01")
  token <- token %||% cdse_token()

  f0 <- paste0(from, "T00:00:00Z")
  f1 <- paste0(to, "T00:00:00Z")

  body <- list(
    input = list(
      bounds = list(
        bbox = bbox,
        properties = list(crs = "http://www.opengis.net/def/crs/EPSG/0/4326")
      ),
      data = list(list(
        type = "sentinel-5p-l2",
        dataFilter = list(timeRange = list(from = f0, to = f1))
      ))
    ),
    aggregation = list(
      timeRange = list(from = f0, to = f1),
      aggregationInterval = list(of = interval),
      evalscript = .ch4_evalscript,
      resx = res, resy = res
    ),
    calculations = list(default = list(statistics = list(default = list())))
  )

  r <- POST(
    Sys.getenv("CDSE_STATS_URL"),
    add_headers(
      Authorization = paste("Bearer", token),
      `Content-Type` = "application/json"
    ),
    body = toJSON(body, auto_unbox = TRUE),
    encode = "raw"
  )
  if (status_code(r) != 200) {
    stop("Erro ", status_code(r), ": ", content(r, "text", encoding = "UTF-8"))
  }

  resp <- content(r, as = "parsed", encoding = "UTF-8")
  df <- do.call(rbind, lapply(resp$data, function(it) {
    st <- it$outputs$data$bands$B0$stats
    data.frame(
      data = as.Date(substr(it$interval$from, 1, 10)),
      ch4_ppb = suppressWarnings(as.numeric(st$mean)),
      n_validos = st$sampleCount - st$noDataCount
    )
  }))
  df$ano <- as.integer(format(df$data, "%Y"))
  df$mes <- as.integer(format(df$data, "%m"))
  df[order(df$data), ]
}

# --- Atalhos por escala -----------------------------------------------------
ch4_diaria <- function(from = "2019-01-01", to = NULL,
                       bbox = brazil_bbox, res = 0.1) {
  if (is.null(to)) to <- as.character(Sys.Date())
  anos <- seq(as.integer(substr(from, 1, 4)), as.integer(substr(to, 1, 4)))
  token <- cdse_token()
  partes <- lapply(anos, function(a) {
    f0 <- as.character(max(as.Date(from), as.Date(paste0(a, "-01-01"))))
    f1 <- as.character(min(as.Date(to), as.Date(paste0(a, "-12-31"))))
    ch4_series("P1D", f0, f1, bbox = bbox, res = res, token = token)
  })
  df <- do.call(rbind, partes)
  df[order(df$data), ]
}

ch4_mensal <- function(from = "2019-01-01", to = NULL,
                       bbox = brazil_bbox, res = 0.1) {
  ch4_series("P1M", from, to, bbox = bbox, res = res)
}

ch4_anual <- function(from = "2019-01-01", to = NULL,
                      bbox = brazil_bbox, res = 0.1) {
  m <- ch4_mensal(from, to, bbox = bbox, res = res)
  m <- m[!is.na(m$ch4_ppb), ]
  agg <- aggregate(ch4_ppb ~ ano, data = m, FUN = mean)
  agg$data <- as.Date(paste0(agg$ano, "-01-01"))
  agg[order(agg$ano), c("data", "ano", "ch4_ppb")]
}
