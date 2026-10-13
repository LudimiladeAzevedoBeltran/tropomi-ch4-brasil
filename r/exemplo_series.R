# ===========================================================================
# Exemplo: séries diária, mensal e anual de CH4 sobre o Brasil (TROPOMI)
#
# Rode da raiz do repositório:
#   Rscript r/exemplo_series.R
#
# Requer: httr, jsonlite (+ dotenv para ler o .env).
# ===========================================================================

source("r/tropomi_ch4.R")

out <- "data"
dir.create(out, showWarnings = FALSE)

# --- Série diária ----------------------------------------------------------
diaria <- ch4_diaria("2019-01-01")
write.csv(diaria, file.path(out, "serie_diaria_ch4_brasil.csv"), row.names = FALSE)
cat("diária:", nrow(diaria), "dias | com dado:",
    sum(!is.na(diaria$ch4_ppb)), "\n")

# --- Série mensal ----------------------------------------------------------
mensal <- ch4_mensal("2019-01-01")
write.csv(mensal, file.path(out, "serie_mensal_ch4_brasil.csv"), row.names = FALSE)
cat("mensal:", nrow(mensal), "meses | com dado:",
    sum(!is.na(mensal$ch4_ppb)), "\n")

# --- Série anual -----------------------------------------------------------
anual <- ch4_anual("2019-01-01")
write.csv(anual, file.path(out, "serie_anual_ch4_brasil.csv"), row.names = FALSE)
print(anual)

# --- Figura (mensal + média anual) -----------------------------------------
png(file.path(out, "serie_mensal_ch4_brasil.png"),
    width = 1100, height = 500, res = 120)
plot(mensal$data, mensal$ch4_ppb, type = "l", col = "grey60",
     xlab = "Ano", ylab = "CH4 (ppb)", main = "CH4 mensal no Brasil — TROPOMI")
lines(anual$data, anual$ch4_ppb, col = "darkred", lwd = 2)
legend("topleft", legend = c("Mensal", "Média anual"),
       col = c("grey60", "darkred"), lty = 1, lwd = c(1, 2), bty = "n")
dev.off()

cat("Arquivos salvos em", normalizePath(out), "\n")
