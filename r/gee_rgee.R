# ===========================================================================
# Google Earth Engine no R via rgee
#
# IMPORTANTE: o GEE consome cota/créditos. Sem cota, as tarefas não rodam ou
# demoram MESES. Rode um mês de teste antes do período todo.
#
# Instalação (uma vez):  install.packages("rgee"); rgee::ee_install()
# ===========================================================================

library(rgee)
ee_Initialize()

brasil <- ee$FeatureCollection("FAO/GAUL/2015/level0")$
  filter(ee$Filter$eq("ADM0_NAME", "Brazil"))$geometry()

banda <- "CH4_column_volume_mixing_ratio_dry_air_bias_corrected"

# Um mês -> GeoTIFF no Google Drive
ini <- ee$Date$fromYMD(2022, 1, 1)
img <- ee$ImageCollection("COPERNICUS/S5P/OFFL/L3_CH4")$
  filterDate(ini, ini$advance(1, "month"))$
  select(banda)$mean()$clip(brasil)$toFloat()

tarefa <- ee_image_to_drive(
  image = img,
  description = "CH4_2022_01",
  folder = "CH4_TROPOMI_Brasil",
  fileNamePrefix = "CH4_2022_01",
  region = brasil$bounds(),
  scale = 1113.2,
  fileFormat = "GeoTIFF"
)
tarefa$start()

cat("Tarefa enviada. Acompanhe em https://code.earthengine.google.com/tasks\n")
