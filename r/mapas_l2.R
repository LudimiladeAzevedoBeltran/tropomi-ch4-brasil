# ===========================================================================
# L2 cru do CDSE (R) -> GeoTIFF mensal (~1 km)
#
# IMPORTANTE: o processo baixa o granule COMPLETO, usa só os pixels da região
# do Brasil e APAGA o arquivo completo. Fica salvo apenas o GeoTIFF recortado.
#
# Requer: httr, jsonlite, ncdf4, terra  (beta / avançado).
# Rode da raiz do repositório:  source("r/mapas_l2.R")
# ===========================================================================

suppressPackageStartupMessages({
  library(httr); library(jsonlite); library(ncdf4); library(terra)
})
if (requireNamespace("dotenv", quietly = TRUE)) dotenv::load_dot_env()

# --- Login da conta (o L2 usa e-mail/senha, não o OAuth client) -------------
l2_token <- function() {
  r <- POST(
    Sys.getenv("CDSE_TOKEN_URL"),
    body = list(grant_type = "password", client_id = "cdse-public",
                username = Sys.getenv("CDSE_USERNAME"),
                password = Sys.getenv("CDSE_PASSWORD")),
    encode = "form"
  )
  if (status_code(r) != 200) stop("Falha no login (", status_code(r), ")")
  content(r, as = "parsed")$access_token
}

.poly <- function(bbox) {
  sprintf("POLYGON((%1$s %2$s,%3$s %2$s,%3$s %4$s,%1$s %4$s,%1$s %2$s))",
          bbox[1], bbox[2], bbox[3], bbox[4])
}

# --- Catálogo OData: lista os granules do mês -------------------------------
l2_granules <- function(ano, mes, bbox = c(-74, -34, -34, 6)) {
  d0 <- sprintf("%04d-%02d-01T00:00:00.000Z", ano, mes)
  d1 <- if (mes == 12) sprintf("%04d-01-01T00:00:00.000Z", ano + 1)
        else sprintf("%04d-%02d-01T00:00:00.000Z", ano, mes + 1)
  filt <- paste0(
    "Collection/Name eq 'SENTINEL-5P' and ",
    "Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and ",
    "att/OData.CSC.StringAttribute/Value eq 'L2__CH4___') and ",
    "ContentDate/Start ge ", d0, " and ContentDate/Start lt ", d1, " and ",
    "OData.CSC.Intersects(area=geography'SRID=4326;", .poly(bbox), "')")

  out <- list(); skip <- 0
  repeat {
    r <- GET(Sys.getenv("CDSE_CATALOG_URL"),
             query = list(`$filter` = filt, `$select` = "Id,Name",
                          `$orderby` = "ContentDate/Start",
                          `$top` = 100, `$skip` = skip))
    stop_for_status(r)
    pg <- content(r, as = "parsed")$value
    out <- c(out, pg)
    if (length(pg) < 100) break
    skip <- skip + 100
  }
  out
}

.find_var <- function(nc, pattern) {
  nm <- names(nc$var)
  hit <- nm[grepl(pattern, nm, ignore.case = TRUE)]
  hit[which.min(nchar(hit))]
}

# Soma ponderada numa grade lon x lat (sem dependência extra)
.bin2d <- function(lon, lat, w, lon_edges, lat_edges) {
  ix <- findInterval(lon, lon_edges)
  iy <- findInterval(lat, lat_edges)
  ok <- ix >= 1 & ix < length(lon_edges) & iy >= 1 & iy < length(lat_edges)
  ix <- ix[ok]; iy <- iy[ok]
  nx <- length(lon_edges) - 1; ny <- length(lat_edges) - 1
  m <- matrix(0, nx, ny)
  if (!length(ix)) return(m)
  idx <- (iy - 1L) * nx + ix
  if (is.null(w)) {
    t <- tabulate(idx, nbins = nx * ny)
    matrix(t, nx, ny)
  } else {
    t <- tapply(w[ok], idx, sum)
    m[as.integer(names(t))] <- as.numeric(t)
    m
  }
}

# --- Acumula um granule na grade -------------------------------------------
.l2_acumular <- function(path, soma, cont, lon_edges, lat_edges, min_qa = 0.5) {
  nc <- nc_open(path); on.exit(nc_close(nc))
  ch4 <- as.vector(ncvar_get(nc, .find_var(nc, "methane_mixing_ratio_bias_corrected")))
  qa  <- as.vector(ncvar_get(nc, .find_var(nc, "qa_value")))
  lat <- as.vector(ncvar_get(nc, .find_var(nc, "latitude")))
  lon <- as.vector(ncvar_get(nc, .find_var(nc, "longitude")))
  ok <- !is.na(ch4) & ch4 > 1000 & ch4 < 3000 & !is.na(qa) & qa >= min_qa &
        abs(lat) <= 90 & abs(lon) <= 180
  if (!any(ok)) return(list(soma = soma, cont = cont))
  soma <- soma + .bin2d(lon[ok], lat[ok], ch4[ok], lon_edges, lat_edges)
  cont <- cont + .bin2d(lon[ok], lat[ok], NULL, lon_edges, lat_edges)
  list(soma = soma, cont = cont)
}

# --- Constrói o GeoTIFF mensal (~1 km) --------------------------------------
l2_mes <- function(ano, mes, out_tif, bbox = c(-74, -34, -34, 6), res = 0.01,
                   min_qa = 0.5, max_granules = NULL) {
  lon_edges <- seq(bbox[1], bbox[3], by = res)
  lat_edges <- seq(bbox[2], bbox[4], by = res)
  soma <- matrix(0, length(lon_edges) - 1, length(lat_edges) - 1)
  cont <- soma

  gr <- l2_granules(ano, mes, bbox)
  if (!is.null(max_granules)) gr <- utils::head(gr, max_granules)
  cat(sprintf("%04d-%02d: %d granules\n", ano, mes, length(gr)))

  tok <- l2_token()
  for (g in gr) {
    fn <- file.path(tempdir(), g$Name)
    try({
      GET(paste0(Sys.getenv("CDSE_DOWNLOAD_URL"), "(", g$Id, ")/$value"),
          add_headers(Authorization = paste("Bearer", tok)),
          write_disk(fn, overwrite = TRUE))
      acc <- .l2_acumular(fn, soma, cont, lon_edges, lat_edges, min_qa)
      soma <- acc$soma; cont <- acc$cont
    }, silent = TRUE)
    if (file.exists(fn)) unlink(fn)          # apaga o arquivo COMPLETO
  }

  media <- soma / ifelse(cont == 0, 1, cont)
  media[cont == 0] <- NA
  # terra: linhas = latitude (de cima p/ baixo), colunas = longitude
  m <- t(media)[nrow(media):1, , drop = FALSE]
  r <- rast(m, extent = ext(bbox[1], bbox[3], bbox[2], bbox[4]),
            crs = "EPSG:4326")
  writeRaster(r, out_tif, overwrite = TRUE, datatype = "FLT4S")
  cat("GeoTIFF:", out_tif, "| CH4 médio:", round(mean(media, na.rm = TRUE), 2), "ppb\n")
  invisible(out_tif)
}

# Exemplo (descomente):
# source("r/mapas_l2.R"); l2_mes(2022, 1, "data/CH4_2022_01.tif", max_granules = 5)
