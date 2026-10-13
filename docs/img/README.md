# Imagens do site

## Já incluídas

| Arquivo | O que é | Onde aparece |
|---|---|---|
| `fluxo.svg` | Diagrama do pipeline (conta + `.env` → séries / mapas) | `index.qmd`, `pt/01`, `en/01` |
| `serie_ch4_brasil.png` | Série mensal real de CH4 sobre o Brasil (2019–hoje) | `index.qmd`, `pt/04`, `en/04` |

## Capturas de tela que você pode adicionar

Salve os arquivos nesta pasta (`docs/img/`) com estes nomes e insira a linha de
markdown onde quiser:

| Arquivo sugerido | O que mostrar |
|---|---|
| `copernicus-register.png` | tela de registro no Copernicus Data Space |
| `copernicus-oauth.png` | *User settings → OAuth clients*, botão **Create** |
| `copernicus-secret.png` | `client_id` + `client_secret` após criar o client |
| `mapa_exemplo.png` | um mapa mensal de CH4 (~1 km) gerado pelo L2 |

Modelo de markdown (ajuste o caminho relativo da página):

```markdown
![Legenda da figura](../img/copernicus-oauth.png){fig-align="center" width="100%"}
```

> Dica: para páginas na raiz (`index.qmd`) use `img/...`; para páginas em `pt/` ou
> `en/`, use `../img/...`.
