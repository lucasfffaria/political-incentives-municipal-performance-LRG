# Social-outcome data by municipality: sources

Collected on 2026-10-08 for the ex-ante evaluation of the mayor-scoring bill.

Every file was downloaded only from `raw.githubusercontent.com`, because government portals (IBGE/SIDRA, DATASUS, INEP, IPEA, SNIS/SINISA) are blocked by the egress policy. Each file is therefore a copy that a third party committed to GitHub, not a direct download from the producing agency. The caveats below say how much each copy was checked against official totals.

* Municipality key: the 7-digit IBGE code.
* Files marked **derived** were produced locally from the raw files in this folder, by format conversion or simple aggregation only. The scripts are not kept in the project.
* The "sha256 (16)" column gives the first 16 hex characters of the file's SHA-256.

---

## 1. Homicides (target 1): partly found, as rates only

| Local path | Exact download URL | Repo page | sha256 (16) |
|---|---|---|---|
| `atlas_violencia/atlas_taxa_homicidios_municipios_1996_2016.csv` | https://raw.githubusercontent.com/vgs2/Socioeconomic-analysis-of-the-brazilian-cities/master/datasets/homicidios.csv | https://github.com/vgs2/Socioeconomic-analysis-of-the-brazilian-cities | 3e07d7fbed2f7e97 |
| `painel_socioambiental/ind/tx_homicidios.json` (also a column of the wide CSV in §7) | https://raw.githubusercontent.com/FelipeCassimiro37/PainelSocioAmbiental/main/dados/ind/tx_homicidios.json | https://github.com/FelipeCassimiro37/PainelSocioAmbiental | 43af1ccd2c7d35e3 |

**Atlas file.** This is an export from the IPEA/FBSP Atlas da Violência (series "homicídios", municipal level), in the Atlas export format `cod;nome;período;valor`. The separator is `;`.
* Coverage: 1996–2016, 5,493 municipalities, 115,353 rows, with no duplicates and no missing values.
* Unit: **homicide rate per 100,000 inhabitants**. The source repo's notebook mislabels it "por 10 mil".
* Sanity check: rate × IBGE population summed over Brazil gives 44,970 homicides in 2000 and 61,528 in 2016. The official SIM/Atlas totals are about 45,400 and 62,500, so the file matches.
* Caveats:
  * The Atlas definition of homicide is ICD-10 X85–Y09 plus Y35–Y36 (legal intervention), by municipality of residence.
  * 78 present-day municipalities are absent, mostly those created after 1996.
  * The file holds rates, not counts. Small municipalities often show a rate of 0 or very high values.
  * The download date and Atlas edition are not documented by the repo author; the year range suggests the 2018 edition.

**IPEA 2022 rate.** This is one value per municipality for 5,570 municipalities, reference year 2022, in homicides per 100,000 inhabitants. The source is cited as "IPEA – Instituto de Pesquisa Econômica Aplicada", i.e. the Atlas da Violência.
* Sanity check: rate × 2022 Census population gives 45,819. The official 2022 figure is about 46,400.
* Caveat: this is a compiled panel fed by a Google Sheet, not the original Atlas export.

**Missing for this target:**
* Municipal series for 2017–2021 and 2023+.
* Counts. These could be approximated as rate × population using `populacao/`, but they would not be the official numerator.

---

## 2. Sanitation (target 2): found

| Local path | Exact download URL | Repo page | sha256 (16) |
|---|---|---|---|
| `snis/br_mdr_snis_municipio_agua_esgoto.csv` | https://raw.githubusercontent.com/juniorcarvalho/painel-saneamento/main/data/br_mdr_snis_municipio_agua_esgoto.csv | https://github.com/juniorcarvalho/painel-saneamento | b649e1da043ce6af |
| `painel_socioambiental/ind/{agua_cob,esgoto_cob,esgoto_trat,perdas,emp_agua,emp_esgoto}.json` | https://raw.githubusercontent.com/FelipeCassimiro37/PainelSocioAmbiental/main/dados/ind/<name>.json | https://github.com/FelipeCassimiro37/PainelSocioAmbiental | see §7 |

**SNIS table.** This is the full Base dos Dados table `br_mdr_snis.municipio_agua_esgoto` (SNIS Água e Esgotos, municipal aggregate).
* Coverage: 119,256 rows × 133 columns, years 1995–2022, 5,549 distinct municipalities. About 5,400 municipalities report in 2020–2022; before 1998 only a few hundred report.
* Key columns:
  * `populacao_atendida_agua` and `populacao_atentida_esgoto` (sic): population served, in persons.
  * `indice_atendimento_total_agua`: IN055, in %.
  * `indice_atendimento_esgoto_agua`: IN056, in %.
  * `indice_coleta_esgoto`: IN015, in %.
  * `indice_tratamento_esgoto`: IN016, treated as a share of collected sewage, in %.
  * `indice_esgotamento_agua_consumida`: IN046, treated sewage as a share of water consumed, in %.
  * The IN codes were mapped by matching national weighted means to the official SNIS figures (below).
* Sanity check for 2022: population served by sewage collection is 112.8 M, i.e. **55.5 % of the population** (official SNIS IN056 is 56.0 %). Water service covers 84.2 % (IN055 weighted mean 84.9 %; official 84.9 %). IN046 weighted mean is 52.5 % (official 52.2 %), IN016 is 82.0 % and IN015 is 64.0 %.
* Caveats:
  * Data are self-reported by service providers.
  * Municipalities without a sewage network have NA in the sewage indices rather than 0. Only 2,900 municipalities have IN056 in 2022.
  * `populacao_urbana` is 0 or missing in 2022.
  * IN023 and IN024 are empty in 2022.
  * The file is a Base dos Dados extract of unknown date that stops at 2022. SINISA replaced SNIS from reference year 2023.

**SINISA panel values.** These come from SINISA (Ministério das Cidades), reference year labelled 2024 in the panel dictionary.
* Indicators: `agua_cob`, `esgoto_cob` and `esgoto_trat`, each in % of population, plus `perdas` (distribution losses, %) and the provider names `emp_agua` and `emp_esgoto`.
* Non-missing municipalities: 5,118 for water, 2,728 for sewage collection and 1,584 for treatment.
* Sanity check: the population-weighted mean of `esgoto_cob` is 67.4 % over reporting municipalities. Treating non-reporters as 0 gives about 54.7 % nationally.
* Caveat: it is ambiguous whether "2024" is the reference year or the publication year.

---

## 3. Favelas / "Favelas e Comunidades Urbanas" (target 3): found (Census 2022)

| Local path | Exact download URL | Repo page | sha256 (16) |
|---|---|---|---|
| `favelas/favelas_demograficos_2022.csv` | https://raw.githubusercontent.com/brunopantaleao/favela_dados/main/favelas_demograficos_2022.csv | https://github.com/brunopantaleao/favela_dados | ffab625cd4d06eb3 |
| `favelas/favelas_ids_ida.csv` (`;` separator, `,` decimal) | https://raw.githubusercontent.com/brunopantaleao/favela_dados/main/favelas_ids_ida.csv | same | 8d52d5867582bace |
| `favelas/README_favela_dados_repo.md` | https://raw.githubusercontent.com/brunopantaleao/favela_dados/main/README.md | same | 0725fc0373cdb443 |
| `favelas/favelas_pop_por_municipio_2022_derivado.csv` (**derived**) | built from the two files above | n/a | 40b5d92db323514f |

* Unit of observation: one row per favela/FCU, 12,348 FCUs in total. The 11-digit code `cd_fcu` begins with the 7-digit municipality code.
* Content: Census 2022 tract data aggregated to the FCU. `pop_setor_total` is persons. `total_pessoas` is persons, `total_dp_ocupados` is occupied households, and the file also has water and sewage connections, literacy, income, and the IDS/IDA indices.
* Coverage: **656 municipalities**, which matches IBGE.
* Sanity check: total population is 16,387,363 (`pop_setor_total`) or 16,349,631 (`total_pessoas`). IBGE's official total is 16,390,815 people in 12,348 FCUs.
* Derived file: one row per municipality with `n_fcu`, the favela population under both definitions, and occupied households (5.56 M).
* Caveat: FCU totals come from census tracts, so they differ slightly from IBGE's official FCU tables.

---

## 4. Literacy at the end of 2nd grade (target 4): found (INEP "Indicador Criança Alfabetizada" 2023–2024)

All files come from https://github.com/tuanyfortunato/predicao-alfabetiza-brasil, under the base URL `https://raw.githubusercontent.com/tuanyfortunato/predicao-alfabetiza-brasil/main/data/`.

| Local path | Source path (appended to the base URL) | sha256 (16) |
|---|---|---|
| `alfabetizacao/silver_resultados_municipio.parquet` | `silver/resultados_municipio.parquet` | caf5447798e445f2 |
| `alfabetizacao/silver_metas.parquet` | `silver/metas.parquet` | 9baf1c8ff1260fa3 |
| `alfabetizacao/gold_indicador_municipio.parquet` | `gold/indicador_municipio.parquet` | bb928d14df9cfe93 |
| `alfabetizacao/gold_meta_vs_resultado.parquet` | `gold/meta_vs_resultado.parquet` | 60f267eecc5acccf |
| `alfabetizacao/gold_evolucao_temporal.parquet` | `gold/evolucao_temporal.parquet` | 59d1b2d5698770c8 |
| `alfabetizacao/ica_resultados_municipio_2023_2024.csv` (**derived**, CSV of the first file) | n/a | a8eaf2e17587846d |
| `alfabetizacao/ica_metas_2023_2025.csv` (**derived**, CSV of `silver_metas`) | n/a | e42257ef99605a59 |
| `alfabetizacao/ica_gold_indicador_municipio_2023_2024.csv` (**derived**, CSV of `gold_indicador_municipio`) | n/a | 90c44825ef208fd6 |

**Main file: `silver_resultados_municipio`.** It is a copy of the Base dos Dados table `br_inep_avaliacao_alfabetizacao.municipio` (INEP).
* Columns: `ano`, `id_municipio`, `serie` (= 2), `rede` (2 = state, 3 = municipal, 5 = public), and `taxa_alfabetizacao` (% of children classed as literate). It also has `media_portugues` (score) and the shares at proficiency levels 0–8.
* Rows: 23,995.
  * 2023: municipal network 5,448 municipalities, public 4,950, state 1,149.
  * 2024: municipal network 5,448 municipalities, public 5,516, state 1,086.
* Sanity check: the national public-network rates in `metas` are 55.9 % (2023), 59.2 % (2024) and 66.0 % (2025, Brazil level only). These match INEP/MEC.
* Caveats:
  * In 2024, 398 Bahia municipalities have extra rows with `rede = 0`. They duplicate `rede = 5` exactly; drop them.
  * The indicator comes from INEP's census-type 2nd-grade assessment, with low participation in some municipalities.
  * The 2025 municipal results are not included.

**Other files.**
* `gold_*` tables were recomputed by the repo authors from the student microdata. They add participation, number of students and children not literate, and a confidence interval.
* `silver_metas` holds the municipal targets for 2024–2030.

---

## 5. Population by age (target 5): **not found by single age**; municipal totals found

| Local path | Exact download URL | Repo page | sha256 (16) |
|---|---|---|---|
| `populacao/brpop_ibge_pop.rds` | https://raw.githubusercontent.com/rfsaldanha/brpop/main/inst/extdata/ibge_pop.rds | https://github.com/rfsaldanha/brpop | a37c86a0e753656f |
| `populacao/ibge_pop_municipios_2000_2025.csv` (**derived**, CSV conversion) | n/a | n/a | 39aaec11b4a43775 |

* Content: IBGE total resident population by municipality, with columns `code_muni`, `year` and `pop`.
* Coverage: 2000–2025, 5,571 municipalities. The sources are the 2000, 2010 and 2022 Censuses, the 2007 Count, the annual estimates (SIDRA 6579), the 2024 DOU estimates and the 2025 TCU estimates.
* Sanity check: 2022 totals 203,080,756, which is the Census figure.
* Caveats:
  * There is **no age breakdown**, so it cannot give the 0–3 or 4–5 population.
  * The brpop age-group series (DataSUS/UFRN) and sustentarea/population-estimates are hosted on Zenodo and OSF, which are blocked.
  * Census 2022 single-age data (SIDRA table 9514) was not found on GitHub.

---

## 6. Child vaccination coverage (target 6): **not found**

No GitHub-hosted municipal PNI coverage file was found. Repos checked include `aureliowozhiak/Projeto_VacinasSalvamVidas` (state level, 1994–2019), the GitHub topic pages `vacinacao`, `cobertura-vacinal` and `pni`, and several DATASUS tool repos.

---

## 7. Lower-priority items (target 7): availability

| Local path | Exact download URL | Repo page | sha256 (16) |
|---|---|---|---|
| `painel_socioambiental/meta.json` | https://raw.githubusercontent.com/FelipeCassimiro37/PainelSocioAmbiental/main/dados/meta.json | https://github.com/FelipeCassimiro37/PainelSocioAmbiental | a54c16e72e359298 |
| `painel_socioambiental/ind/<indicator>.json` (24 files) | https://raw.githubusercontent.com/FelipeCassimiro37/PainelSocioAmbiental/main/dados/ind/<indicator>.json | same | see the listing in this file's folder |
| `painel_socioambiental/README_repo.md` | https://raw.githubusercontent.com/FelipeCassimiro37/PainelSocioAmbiental/main/README.md | same | 85d2ee7caafd7776 |
| `painel_socioambiental/painel_socioambiental_municipios_wide.csv` (**derived**: one row per municipality, one column per downloaded indicator) | n/a | n/a | b63122eb830d5305 |

**Panel structure.**
* Each `ind/*.json` file is an array aligned with `meta.json["municipios"]`, which lists 5,571 IBGE codes.
* `meta.json` holds the dictionary: name, unit, year and source for each indicator. The panel version is `5df89e76dcf8`, updated 04/09/2026.
* The panel is compiled by its author from a Google Sheet, so it is a secondary source.

**Robberies.** These cover 2023, come from the state security secretariats, and are in occurrences and per 100,000 inhabitants.
* Indicators: `roubos_total` and `tx_roubos`, plus a breakdown into transeunte, veículo, carga, comércio, residência, banco, coletivo, celular, outros, agravado and lesão. Also included are `estupro` and `tent_homicidio`, which are available only for Bahia.
* Coverage: 2,477 municipalities, all in 10 states: BA, DF, ES, MG, PA, PE, PR, RJ, RO and SP.
* Caveat: crime definitions differ between states.

**Not found:**
* SIH hospitalisations for assault against women by municipality.
* SISREG waiting times. These are not published nationally.
* SINESP-VDE municipal series. Only state-level copies were found.

---

## Other candidates checked and rejected
* `eduardo-batista7/painel-saude-municipal` (2013–2019): SIM deaths only by ICD letter, and SNIS fields.
* `jairojuunior/brazil_mortality_datasus_processor`: ICD chapters only.
* `lspassos1/mapa-da-violencia-brasil`: SIM and SINESP data only at state level.
* `rafa-trindade/flor-de-aco-foundation`: female X85–Y09 microdata, but on Kaggle only.
* `tiagoazv/ml-homicide-risk-prediction`: Atlas data for 2000–2024 is gitignored.
* `kahefl/Homicidios-Brasil`: SINESP data at state level.
* `openwashdata/wsabrazil`: 2010 Census tract data.

The search stopped early for targets 5–7 because the shared web-search budget ran out.

### Checksums of `painel_socioambiental/ind/*.json` (sha256, first 16 hex characters)

- `agua_cob.json`: 85ddc5ea243f39b7, 32385 bytes
- `emp_agua.json`: b174ad662cd1c4b4, 244806 bytes
- `emp_esgoto.json`: 786ca9889914336d, 145750 bytes
- `esgoto_cob.json`: b65c20d14842801e, 30060 bytes
- `esgoto_trat.json`: b68fd74f38e8a2e8, 28883 bytes
- `estupro.json`: 156488987d9547a4, 26746 bytes
- `perdas.json`: 193dd4dbc15d86de, 32049 bytes
- `pop_total.json`: aac6bdcffb0bfa0d, 31264 bytes
- `roubo_agravado.json`: 85d0b7ad078814e8, 26939 bytes
- `roubo_banco.json`: 72b5e271e9d3aeb4, 24230 bytes
- `roubo_carga.json`: d5f53cafac134254, 22676 bytes
- `roubo_celular.json`: 393eb16b5e31ed89, 27364 bytes
- `roubo_coletivo.json`: 9fa1483d8b01deee, 24599 bytes
- `roubo_comercio.json`: 299c422a17c1e488, 25559 bytes
- `roubo_lesao.json`: 58658a0a577b1cbb, 26892 bytes
- `roubo_outros.json`: 5df995c4e15b8830, 24101 bytes
- `roubo_residencia.json`: 1b8a3480ae6ae247, 24249 bytes
- `roubo_transeunte.json`: 07dbe24319e877b1, 24410 bytes
- `roubo_veiculo.json`: 17b80227a58055cc, 22739 bytes
- `roubos_total.json`: 1b5019c1b7ea0ca9, 21746 bytes
- `taxa_analf.json`: 25d64cd04901292b, 29943 bytes
- `tent_homicidio.json`: c3912e14edfaa892, 26691 bytes
- `tx_homicidios.json`: 43af1ccd2c7d35e3, 29120 bytes
- `tx_roubos.json`: 6875259ea54fe91b, 30110 bytes
