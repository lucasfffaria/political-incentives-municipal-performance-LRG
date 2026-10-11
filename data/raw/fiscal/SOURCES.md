# Fiscal / economic raw data: sources and provenance

Collected on 2026-10-08 for the ex-ante evaluation of the proposed law on municipal performance, federal transfers and mergers of municipalities.

**How it was collected.** Outbound network access was limited to `raw.githubusercontent.com`, `media.githubusercontent.com` and PyPI. Every file below was downloaded from a public GitHub repository through `raw.githubusercontent.com`. Government portals (IBGE, SICONFI, Tesouro, MDS, Portal da Transparência), Firjan, Base dos Dados/BigQuery, Kaggle, Zenodo and Dataverse were not reachable. All files are copies or aggregations of official data made by third parties. Check them against the official source before publication.

The WebSearch budget for the session ran out after about 45 queries. A follow-up session could search further for full FINBRA/DCA, IFGF and FPM files.

Municipality key: 7-digit IBGE code in every file. Money values are in nominal R$ (current prices) unless a file says otherwise.

## Status by target

| # | Target | Status | Main file(s) |
|---|---|---|---|
| 1 | Municipal public finance | **Partial.** SICONFI RREO/RGF, 2019–2024, about 58% of municipalities and few large ones missing. No FINBRA/DCA item detail (IPTU, ISS, ITBI, FPM, ICMS). No Firjan IFGF. | `siconfi_rreo_rgf/` |
| 2 | Municipal GDP by sector | **Found.** Official IBGE file. Sector value added for 2010–2021; total GDP for 2010–2023. | `pib_municipios/` |
| 3 | Formal employment | **Found.** RAIS stock on 31 Dec, 2006–2024, split by sector; RAIS 2025 snapshot; IBGE CEMPRE 2024. | `rais_municipal/`, `emprego_bolsafamilia/`, `ibge_cempre_censo/` |
| 4 | Bolsa Família / CadÚnico | **Found, two points in time.** May 2024 and Dec 2025, plus CadÚnico people in Bolsa Família families for Dec 2025. | `emprego_bolsafamilia/` |
| 5 | FPM transfers and coefficients | **Not found.** Only the TCU population estimates that the FPM coefficients are based on. | `populacao_tcu/` |

---

## 1. `pib_municipios/`: IBGE PIB dos Municípios 2010–2023

### `pib_municipios/PIB_dos_Municipios_base_de_dados_2010-2023.xlsx` (raw, unchanged)
- **URL:** https://raw.githubusercontent.com/DanielNego/projeto-bi-pib-municipios/main/dados/PIB%20dos%20Munic%C3%ADpios%20-%20base%20de%20dados%202010-2023.xlsx
- **Repo:** https://github.com/DanielNego/projeto-bi-pib-municipios
- **Original:** IBGE, https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html (release of Dec 2025)
- **SHA-256:** `7bf207208d08805eed3d74ad8e71a5967ea7eb333be0adf007d4942c1697e47a`
- **Contents:** sheet "PIB dos Municípios" (77,965 rows × 43 columns) and sheet "Notas". Columns:
  - territorial classifications: region, UF, meso/micro region, immediate/intermediate region, urban hierarchy, Amazônia Legal, Semiárido
  - gross value added (VAB) for agriculture, industry, services excluding public administration, and public administration ("Administração, defesa, educação e saúde públicas e seguridade social")
  - total VAB, taxes net of subsidies, PIB, PIB per capita
  - the top three activities by value added
- **Units:** R$ 1,000 at current prices. PIB per capita in R$.
- **Coverage:** 5,565 municipalities for 2010–2012 and 5,570 for 2013–2023.
- **Checks:**
  - The sum of municipal PIB is R$ 9.012 trillion in 2021 and R$ 10.943 trillion in 2023. Both match national GDP.
  - São Paulo has the largest PIB (R$ 1.067 trillion in 2023).
  - In 2021 the median share of public administration in VAB is 26.8%. It exceeds 50% in 935 municipalities.
- **Caveats:**
  - **For 2022 and 2023 IBGE released only PIB and PIB per capita.** The VAB columns are empty for those years (IBGE Nota Técnica 02/2024).
  - The 2022–2023 figures are subject to revision.
  - The population behind PIB per capita is the TCU estimate for 2010–2021, the first Census 2022 count for 2022, and the 2023 TCU list for 2023.

### `pib_municipios/pib_municipios_2010_2023_slim.csv` (derived)
- Long CSV with one row per year and municipality, built by `_scripts/final_conv.py`.
- Columns: `ano, cod_uf, sigla_uf, cod_ibge, nome_municipio, amazonia_legal, semiarido, hierarquia_urbana, vab_agropecuaria, vab_industria, vab_servicos_exc_adm_publica, vab_adm_publica_defesa_educ_saude_seg_social, vab_total, impostos_liq_subsidios, pib, pib_per_capita_reais, populacao_implicita`.
- Units are the same as the xlsx. `populacao_implicita = pib*1000/pib_per_capita`.

## 2. `rais_municipal/`: RAIS formal jobs by municipality, 2006–2024

### `rais_municipal/raw_bin/` (raw, unchanged)
- **Files and URLs:**
  - `mun_{2006..2024}.bin.gz` from `https://raw.githubusercontent.com/rafapolo/rais/main/docs/data/mun/{YEAR}.bin.gz`
  - `municipios.json.gz` from https://raw.githubusercontent.com/rafapolo/rais/main/docs/data/municipios.json.gz
  - `meta.json` from https://raw.githubusercontent.com/rafapolo/rais/main/docs/data/meta.json
- **Repo:** https://github.com/rafapolo/rais (browser explorer at https://rafapolo.github.io/rais/)
- **Code that built them:** `pipeline/extrai.py` and `pipeline/constroi.py` in the repo.
- **Origin:** Base dos Dados table `br_me_rais.microdados_vinculos`, aggregated by the repo author.
- **Format:** a gzipped columnar binary. It contains `[u32 header length][JSON header][8-byte aligned columns]`, and 32-bit columns are stored byte-planar.
- **Cells:** year × municipality (index into `municipios.json.gz`) × sector × CNAE section × sex.
- **Measures:**
  - `ativos`: jobs with `vinculo_ativo_3112 = 1`, i.e. active on 31 Dec
  - `adm`: hires during the year
  - `desl`: separations during the year
  - `rem_m`: mean nominal December pay in R$
  - `rem_f`: active jobs without December pay
- **Sector** comes from the first digit of the employer's natureza jurídica: 1 = public administration, 2 = businesses (including state-owned companies), 3 = non-profits and others.

### `rais_municipal/rais_vinculos_municipio_setor_2006_2024.csv` (derived, `_scripts/decode_rais.py`)
- 105,791 rows, one per year and municipality, keyed by `id_municipio`.
- **Columns:**
  - `ativos_total`, `ativos_adm_publica`, `ativos_empresas`, `ativos_sem_fins_outros`
  - `admissoes`, `desligamentos`
  - `rem_n_*`: number of active jobs with December pay
  - `rem_dez_soma_*`: total December pay in nominal R$, computed as `rem_m × rem_n`. Because `rem_m` is rounded to whole reais, each cell can be off by up to R$ 0.50 per job.
- **Coverage:** 5,562–5,565 municipalities for 2006–2012, 5,570 for 2013–2022, 5,571 for 2023–2024.
- **Checks:**
  - Total active jobs: 35.2M (2006), 46.7M (2019), 52.8M (2022), 57.8M (2024). These match the published RAIS totals.
  - Public administration jobs: 8.2M (2006), 9.8M (2022), 11.4M (2023), 11.7M (2024).
  - São Paulo is the largest, with 5.43M jobs in 2024.
- **Caveats:**
  - Jobs are counted where the establishment is located.
  - Public-administration jobs jump in 2023 (+1.6M). This is likely a reporting change (public bodies moving to eSocial), not real growth.
  - Employees under special regimes (statutory servants) are in RAIS, but their coverage has varied over time.

## 3. `emprego_bolsafamilia/`: RAIS 2025, Bolsa Família and CadÚnico, plus Bolsa Família May 2024

### `folha_mun_202512_site_dados.json`, `folha_mun_202512_site_municipios.json`, `folha_mun_202512_dicionario.md`, `folha_mun_202512_validacao.md` (raw, unchanged)
- **URLs:**
  - https://raw.githubusercontent.com/jorgel-mendes/folha-pagamento-municipios/main/site/dados.json
  - https://raw.githubusercontent.com/jorgel-mendes/folha-pagamento-municipios/main/site/municipios.json
  - https://raw.githubusercontent.com/jorgel-mendes/folha-pagamento-municipios/main/dados/gold/202512/dicionario.md
  - https://raw.githubusercontent.com/jorgel-mendes/folha-pagamento-municipios/main/dados/gold/202512/validacao.md
- **Repo:** https://github.com/jorgel-mendes/folha-pagamento-municipios (pipeline in `pipeline/`). The full gold CSV/parquet is git-ignored and was not available.
- **Sources and reference month (Dec 2025):**
  - RAIS 2025 microdata from PDET: active jobs on 31 Dec 2025
  - INSS benefits issued
  - Portal da Transparência Bolsa Família payments for Dec 2025
  - CadÚnico from SAGI/MDS
  - DATASUS POPSVS population

### `folha_mun_202512_flat.csv` (derived, `_scripts/flatten_folha.py`)
- 5,571 municipalities, one row each.
- **Columns:**
  - `salario_privado_n`: private RAIS jobs
  - `salario_publico_n`: public RAIS jobs, natureza jurídica 1xxx
  - `salario_publico_n_municipal`, `_estadual`, `_federal`: public jobs by level of government
  - `bolsa_familia_n`: families
  - `bolsa_familia_massa`: R$ per month
  - `bolsa_familia_pessoas`: CadÚnico people in Bolsa Família families
  - `previdencia_n`, `previdencia_massa`: INSS benefits and R$ per month
  - wage bills (`*_massa`, R$ per month), `pop`, `pop18`
- **Checks:**
  - RAIS jobs: 45.13M private and 13.40M public (7.69M municipal, 4.31M state, 1.37M federal).
  - Bolsa Família: 18.48M families, R$ 12.52 bn in the month, 49.2M people.
  - INSS: 41.18M benefits. This is within +0.01% of the official INSS total.
  - São Paulo has the most Bolsa Família families (610k).
- **Caveats:**
  - This is a third-party aggregation.
  - RAIS "abandoned" jobs and jobs with unknown natureza jurídica are excluded.
  - Bolsa Família municipalities are matched from SIAFI to IBGE codes by name, including fuzzy matching.
  - Unit counts differ by source (jobs, benefits, families) and must not be added together.
  - `salario_publico_massa` is a hybrid measure (see the dictionary).
  - INSS is counted by the municipality of residence; RAIS by the municipality of the establishment.
  - Values in the site JSON are rounded.
  - Four municipalities have one source suppressed (`supressoes` column).

### `bolsa_familia_mun_202405.parquet` (raw, unchanged) and `bolsa_familia_mun_202405.csv` (derived, `_scripts/final_conv.py`)
- **URL:** https://raw.githubusercontent.com/nicolas-sds/MVP-EngenhariadeDados/main/data/bolsa_familia_brasil.parquet
- **Repo:** https://github.com/nicolas-sds/MVP-EngenhariadeDados (extraction script `scripts_auxiliares/extrair_dados.py`)
- **Contents:** Novo Bolsa Família payments for May 2024 (`mes_referencia` = 202405) from Portal da Transparência microdata, aggregated by municipality. Columns: number of payment records (≈ families) and total R$.
- **Coverage:** 5,570 municipalities.
- **Checks:**
  - 20.50M payments, R$ 13.46 bn.
  - São Paulo is the largest (685k).
- **Caveats:**
  - The count is the number of payment rows, not unique families, so retroactive installments could double-count.
  - SIAFI→IBGE matching was done by name: 22 fuzzy matches and 9 static mappings.

## 4. `siconfi_rreo_rgf/`: SICONFI RREO and RGF extracts (partial coverage)

### `painel_fiscal_snapshot_raw.json` (raw, unchanged)
- **URL:** https://raw.githubusercontent.com/peterwkdev-creator/painel-fiscal-ne/main/painel/dados/snapshot.json
- **Repo:** https://github.com/peterwkdev-creator/painel-fiscal-ne (collector code in `fiscal/siconfi.py`)
- **Origin:** SICONFI API (apidatalake.tesouro.gov.br), queried for every municipality in Sep 2026.

### Derived CSVs (`_scripts/tidy_painel_fiscal.py`)
- **`siconfi_rgf_anexo01_pessoal_2024q3.csv`**: RGF Anexo 01 for the municipal Executive, 3rd four-month period of 2024 (the last 12 months).
  - Columns: personnel expenditure (R$), adjusted RCL (R$), and the share of personnel expenditure in adjusted RCL as filed. Also the prudential limit and population.
  - 5,570 rows, of which 3,244 have data (`publicou`).
  - Checks: São Paulo has personnel expenditure of R$ 26.4 bn against an adjusted RCL of R$ 93.2 bn (28.4%). 361 municipalities are above 54%.
- **`siconfi_rgf_anexo01_pct_pessoal_serie_2020_2024.csv`**: personnel share of RCL only, for the 15 four-month periods of 2020–2024. 3,814 municipalities, about 3,200–3,370 per period.
- **`siconfi_rreo_anexo01_receitas_correntes_2024.csv`**: RREO Anexo 01, column "Até o Bimestre (c)" for the 6th two-month period, i.e. full-year 2024 realized current revenue. 3,243 municipalities.
  - Columns: total current revenue, and its 8 components (current transfers; taxes, fees and improvement contributions; property income; contributions; other; services; industrial; agricultural).
  - Detail columns: `det_impostos`, `det_taxas`, `det_transferencias_da_uniao...`, `det_transferencias_dos_estados...`.
  - Checks: the components add up to the declared total (difference ≤ R$ 2). São Paulo has the largest tax revenue (R$ 61.1 bn). Total current revenue across the covered municipalities is R$ 1.056 trillion.
- **`siconfi_rreo_anexo02_despesa_funcao_2019_2024.csv`**: liquidated expenditure ("DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)", 6th period) by budget function (28 functions plus the declared total). 3,240–3,452 municipalities per year.
- **`siops_pct_recursos_proprios_saude_2000_2025.csv`**: SIOPS indicator 3.2, the share of own revenue applied to health (EC 29). 5,568 municipalities, 2000–2025.

### Caveats (important)
- **Coverage is not random.** About 100% of municipalities above 50k inhabitants are covered, compared with 40% at or below 5k and 49% at 5–10k. The collector queried only the four-monthly RGF (`in_periodicidade=Q`, `co_tipo_demonstrativo=RGF`) and the full `RREO` (`fiscal/siconfi.py`). Municipalities under 50k that chose six-monthly or simplified reporting are therefore missing.
- There is no breakdown of IPTU, ISS, ITBI, FPM or ICMS. "Transferências da União" mixes FPM, SUS, FNDE and other transfers.
- Values are nominal R$ and are the figures filed by each municipality.
- The personnel share is the one filed by the municipality, not recomputed.

## 5. `ibge_cempre_censo/`: IBGE CEMPRE 2024 and Census 2022 indicators

### `numeros_publicos_ibge_snapshot_raw.json` (raw, unchanged) and derived files
- **URL:** https://raw.githubusercontent.com/peterwkdev-creator/numeros-publicos/main/painel/dados/snapshot.json
- **Repo:** https://github.com/peterwkdev-creator/numeros-publicos
- **Origin:** IBGE SIDRA API. The table and variable for each indicator are listed in `ibge_indicadores_metadados.csv`, which includes the exact API URLs.
- **Derived file:** `ibge_cempre2024_censo2022_municipios.csv` (`_scripts/tidy_np.py`), 5,571 rows. The column suffix gives the reference year.
  - CEMPRE 2024 (table 9509): companies and organizations, total employed, salaried employees, average salaried employees, wages (R$ 1,000), average wage.
  - Census 2022: labour force, occupied, contributors, income mass, basic services, education.
  - PIB 2023 (table 5938).
  - Population: Census 2022 and the 2026 estimate.
- **Checks:**
  - Salaried employees in 2024: 54.2M. Total employed: 68.0M.
  - Census 2022 population: 203.08M, which matches the official count.
  - PIB 2023 matches the IBGE workbook.
- **Caveats:** CEMPRE counts all CNPJ-registered organizations, so public administration bodies are included. Boa Esperança do Norte (MT) has no CEMPRE data.

## 6. `populacao_tcu/`: IBGE population estimates sent to TCU (the basis of FPM coefficients)

### `poptcu2010-2022_2024.long.csv`, `popBR_mun_README.md` (raw, unchanged)
- **URLs:**
  - https://raw.githubusercontent.com/lsbastos/popBR_mun/master/poptcu2010-2022_2024.long.csv
  - https://raw.githubusercontent.com/lsbastos/popBR_mun/master/README.md
- **Repo:** https://github.com/lsbastos/popBR_mun
- **Contents:** 77,980 rows, covering 5,570 municipalities × years 2010–2022 and 2024. 2023 is absent because no estimate was released that year and the Census 2022 count was used instead.
- **Checks:** São Paulo is 11,253,503 in 2010 (Census) and 11,895,578 in 2024.
- **Caveats:**
  - The 2022 values are the figures sent to TCU in Dec 2022 from the preliminary census, not the final Census count.
  - 12 values are missing (municipalities created in 2013 have no 2010–2011 values, and Jacareacanga has none for 2014).
  - FPM coefficients are **not** in this file. FPM-Interior coefficients could be rebuilt from these populations using the brackets in DL 1.881/1981 and the state shares, but that is an analysis step.

---

## Not found, and leads for a follow-up
- **FINBRA / SICONFI DCA (Anexo I-C, with IPTU, ISS, ITBI, taxes, FPM, ICMS) for all municipalities, and Firjan IFGF:**
  - No GitHub-hosted full-coverage file was found.
  - Base dos Dados has `br_me_siconfi.municipio_receitas_orcamentarias` and `br_firjan_ifgf.ranking`, but they are on BigQuery, which is blocked here.
  - `github.com/tchiluanda/municipios` (Tesouro staff) works with FINBRA 2023 (Anexos I-C, I-D, I-E), but its `data/` folder could not be listed (robots-blocked) and only a Paraná file is visible.
  - `github.com/hilaliskandar/mapa_do_tesouro` covers SP only, and its data are in a private bucket.
- **FPM by municipality and FPM coefficients (TCU Decisão Normativa):** not found.
  - `github.com/monitorelnino/monitorelnino` has `data/financiamento/municipios/transferencias_uniao.json`, with 2026 Union transfers from Portal da Transparência. Its "constitucional" route mixes FPM, Fundeb, royalties and other items, adding to about R$ 232 bn for Jan–Aug, so it is not usable as FPM. It was **not saved**.
- **Considered but not saved (redundant):** `github.com/gukse/dados-coop` (`dados/tratados/municipios.csv`, `empresas_setor.csv`, `caged_mensal.csv`). It has CAGED flows for Sep 2025–Aug 2026 and CEMPRE by CNAE division for only 682 municipalities.
