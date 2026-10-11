# Elections, mayors, Chamber 2022 and amendments: sources

Collected on 2026-10-08. Downloads came only from `raw.githubusercontent.com` or `media.githubusercontent.com` (Git LFS). Two small tables were read with WebFetch from cached English Wikipedia pages. Government portals (TSE, Câmara, Portal da Transparência, CEM-USP) and Hugging Face were not used. Most of these files are copies or derivatives of official TSE or Transferegov data published by third parties in GitHub repositories. Treat them as secondary sources and cite the original producer (TSE or Transferegov) together with the repository.

Party labels follow TSE at the time of each election. Mergers to keep in mind: DEM+PSL became UNIÃO (2022), PTB+PATRIOTA became PRD (2023), PSC joined PODE (2023), PROS joined SOLIDARIEDADE (2023). In 2016 the labels are already recoded to their 2020 names; see section 1.4.

The scripts that build the derived tables are in `_scripts/`. Run each one as `python3 -I <script> /home/claude/lrg2/data/raw/elections`. Run `build_camara2022.py` with the `camara_2022_kalebefukuda` folder as the argument.

---------------------------------------------------------------------------------------------------

## 1. Mayors (target 1)

### 1.1 `tse_2024_votacao_pedrovitorsilva/votacao_candidato_munzona_2024_brasil.parquet`  (PRIMARY 2024 SOURCE)
- **What it is:** the official TSE file "Votação nominal por candidato, município e zona" for 2024 (`votacao_candidato_munzona_2024_BRASIL`), converted from CSV to Parquet without filtering (the repo's `csv_to_parquet.py` only does a type-preserving conversion). The TSE generated it on `DT_GERACAO = 16/09/2026`, so it already includes later re-totalizations and supplementary elections.
- **Download URL (Git LFS zip, 460,630,867 bytes, sha256 7d55af25d6a9472b1f08e7fe3eb3723c584098df64db4e50ca8e111b8ba572b3, matches the LFS oid):**
  `https://media.githubusercontent.com/media/pedrovitorsilva/eleicoes-2024/main/parquet.zip`
  I extracted the member `parquet/votacao_candidato_munzona_2024_brasil.parquet` and then deleted the zip. The zip's other members (campaign expenses, party revenues, and `perfil_eleitorado_2024_brasil.parquet` with the electorate profile by municipality) were not kept. Re-download the zip if you need them.
- **Repo:** https://github.com/pedrovitorsilva/eleicoes-2024 (Power BI dashboard; README credits the TSE Portal de Dados Abertos)
- **Size:** 717,195 rows × 50 columns (all TSE columns, for example SQ_CANDIDATO, NM_CANDIDATO, NM_URNA_CANDIDATO, SG_PARTIDO, SG_FEDERACAO, DS_COMPOSICAO_COLIGACAO, QT_VOTOS_NOMINAIS(_VALIDOS), DS_SIT_TOT_TURNO, DS_SITUACAO_CASSACAO). Prefeito: 19,118 rows; vereador: 698,077 rows.
- **Coverage:**
  - Ordinary election, 1st round (CD_ELEICAO 619) and 2nd round (CD_ELEICAO 620, 51 municipalities). It also contains 34 supplementary mayoral elections (06/04/2025–21/06/2026) and 2 supplementary council elections.
  - Prefeito rows exist for 5,561 of the 5,569 municipalities that held elections.
  - Party counts of winners in the ordinary election (5,531 municipalities): PSD 886, MDB 859, PP 747, UNIÃO 588, PL 515, REPUBLICANOS 434, PSB 311, PSDB 272, PT 252, PDT 151. These match the expected ranges.
- **Caveats (gaps in the TSE file as published):**
  - 8 municipalities have no rows at all: Americano do Brasil and Iporá (GO); Anajatuba, Guimarães and Santana do Maranhão (MA); Barra dos Coqueiros, Cedro de São João and Nossa Senhora do Socorro (SE).
  - Aracaju has only 2nd-round rows.
  - Vereador rows cover only 5,546 municipalities.
  - 30 municipalities have no `ELEITO` in the ordinary election (results annulled or sub judice). 22 of them have a winner in a later supplementary election. The other 8 have no winner yet: Mercês, Tucuruí, Itaguaí, São Miguel do Gostoso, Macedônia, Martinópolis, Narandiba and Sarutaiá.
  - 12 more municipalities held a supplementary election after the ordinary winner was removed.
  - The file has no incumbency (`ST_REELEICAO`) and no candidate profile; these are in `consulta_cand`, which was not found.
- **Also kept:** `tse_2024_votacao_pedrovitorsilva/partidos_tse_pagina1.parquet`, a 30-row party registry from the same zip (sigla, name, legend number).

### 1.2 `marcofaga_2020/prefeito2020.csv`  (2020, 1st round)
- **URL:** https://raw.githubusercontent.com/marcofaga/eleicoes2020/master/prefeito2020.csv (`README_repo.md` comes from the same repo)
- **Repo:** https://github.com/marcofaga/eleicoes2020
- **What it is:** candidate-level mayoral results of the 15/11/2020 first round, scraped from the TSE results JSON on election night ("divulgação oficial"). It is `;`-separated and has 18,635 rows and 19 columns: codele, codtse (TSE code), codibge, uf, nomemun, ncand, nomeurna, partido, votosabs, votosporc (TSE % of valid votes), situacao (ELEITO / NAO ELEITO / 2O TURNO), apuracao and others.
- **Coverage:** 5,567 municipalities. Mandirituba (PR) is absent. Macapá is present with 0% counted, because its election was postponed.
- **Caveats:**
  - First round only, as published that night. 5,403 municipalities have an `ELEITO`. 57 went to a 2nd round, whose winner is not in the file. 107 had no decided winner (sub judice).
  - Later court decisions are not reflected.
  - Only ballot names (no full names or CPF).
  - First-round winners by party: MDB 772, PP 681, PSD 649, PSDB 512, DEM 459, PL 345. The final 2020 counts after both rounds were MDB 784, PP 685, PSD 654, PSDB 520, DEM 464.

### 1.3 `herrmann_2020/planos-de-governo.csv`  (2020 candidates: incumbency flag and profile)
- **URL:** https://raw.githubusercontent.com/augusto-herrmann/eleicoes-2020-planos-de-governo/main/dados/planos-de-governo.csv
- **Repo:** https://github.com/augusto-herrmann/eleicoes-2020-planos-de-governo (data from the TSE DivulgaCandContas API)
- **What it is:** 19,341 mayoral candidates (2020) in 5,568 municipalities. Columns: codigo_cidade_tse, municipio, sigla_estado, codigo_candidato (SQ_CANDIDATO), nome_urna, sigla_partido, data_nascimento, cor_raca, genero, estado_civil, grau_instrucao, ocupacao, candidato_reeleicao (S/N), plus the plan URL and file.
- **Caveats:**
  - `sigla_partido` is missing for 915 rows (whole states such as PE and SE).
  - `candidato_reeleicao` = S for only 1,713 candidates, which looks like an undercount. Among 2020 winners, 1,146 are flagged N but are the same person (CPF) as the 2016 winner. Prefer the CPF-based flag in the derived 2020 table.

### 1.4 `pindograma_2016/prefeitos_longevos.Rdata`  (2016 winners)
- **URL:** https://raw.githubusercontent.com/pindograma/materias/master/2020-10-26-prefeitos-longevos/data/prefeitos_longevos.Rdata (`prefeitos-longevos.Rmd` is the article source from the same folder)
- **Repo:** https://github.com/pindograma/materias (Pindograma data journalism; data under ODbL, built from TSE candidate files)
- **What it is:** R objects. The two used here are:
  - `prefeitos`: elected mayors with ANO_ELEICAO, UF, MUNICIPIO (name, no accents), CANDIDATO, NOME_URNA, CPF, PARTIDO, OCUPACAO, SEXO, IDADE, COMPOSICAO_LEGENDA, plus municipal covariates. 2016 has 5,562 rows covering 5,551 municipalities. Earlier years (1996–2012) are incomplete; use 2016 only.
  - `candidatos`: 18,917 mayoral candidates of 2020 with CPF and age.
- **Caveats:**
  - There are no municipality codes; the derived table maps names to TSE codes with 100% success.
  - There are no votes.
  - PARTIDO is recoded to 2020 party names (PMDB→MDB, PR→PL, PRB→REPUBLICANOS, PPS→CIDADANIA, and so on).
  - 11 municipalities have two winners (supplementary elections; no date to tell them apart).
  - One age is an obvious error (967); it is set to NA in the derived table.
  - Party counts: MDB 1,049, PSDB 805, PSD 540, PP 498, PSB 409. These are close to the official post-runoff 2016 figures plus supplementary elections.
  - The file contains CPF, which is personal data published by the TSE. The derived CSVs do not include CPF.
- **Reading the file:** it needs the `rdata` Python package (`pyreadr` fails on it) or R.

### 1.5 `crosswalk/municipios_brasileiros_tse.csv` and `crosswalk/municipios_tse_ibge_2024.csv`
- **URL:** https://raw.githubusercontent.com/betafcc/Municipios-Brasileiros-TSE/master/municipios_brasileiros_tse.csv
- **Repo:** https://github.com/betafcc/Municipios-Brasileiros-TSE
- **What it is:** the TSE↔IBGE code crosswalk, 5,570 rows (built in 2018; includes Brasília and Fernando de Noronha).
- **`municipios_tse_ibge_2024.csv`:** the same table plus Boa Esperança do Norte (MT), TSE code 73709 → IBGE 5101837. The TSE code comes from the 2024 TSE file. The IBGE code comes from the IBGE-based files in `../fiscal/`.

### 1.6 Derived tables (`derived/`, built by `_scripts/build_mayors.py`)

**`prefeitos_2024_municipio.csv`** (5,569 rows, one per municipality; TSE and IBGE codes)
- Results: candidates in the 1st round, valid votes, 2nd-round flag, winner (SQ, full name, ballot name, party, federation, coalition, cassação status), winner votes and share in the 1st, 2nd and final round, runner-up party and share, and margin.
- Supplementary elections: winner and date of the last one.
- `status_2024`: `eleito_na_ordinaria`, `sem_eleito_na_ordinaria` or `ausente_no_arquivo_tse`.
- 2020 winner of the municipality: party and names.
- `reeleito_proxy`: 1 if the 2024 winner has the same full name, or failing that the same ballot name, as the 2020 winner. Result: 2,244 yes, 3,145 no, 180 NA. This is a proxy. It does not count vice-mayors who took office, and it is NA where the 2020 winner is unknown.

**`prefeito_2024_candidatos_municipio.csv`**
- 15,216 candidate × round rows (votes summed over zones), covering all prefeito candidates in the ordinary and supplementary elections.

**`prefeitos_2020_municipio_1turno.csv`** (5,567 rows)
- Results from marcofaga: 1st-round winner, party, votes and TSE share; top-2 candidates; margin; `status_2020`.
- Winner profile and `eleito_candidato_reeleicao` from Herrmann; 5,402 of 5,403 winners matched.
- `eleito_2020_igual_eleito_2016_cpf`: 1,998 yes, 3,322 no, 247 NA. This is the CPF link through Pindograma.
- `eleito_final_sg_partido` adds the winners for 19 capitals from Wikipedia: 18 runoff capitals plus Macapá. 38 non-capital runoff municipalities and 107 sub judice municipalities remain unknown.

**`prefeitos_2020_capitais_wikipedia.csv`**
- 26 capitals with the 2020 winner, party, vice-mayor and the vice-mayor's party.
- Read with WebFetch from https://en.wikipedia.org/wiki/2020_Brazilian_municipal_elections (cached copy).
- Wikipedia is a secondary source.

**`prefeitos_2016_eleitos.csv`** (5,562 rows)
- 2016 winners with TSE and IBGE codes, names, recoded party, coalition, occupation, gender and age.
- `eleito_2016_candidato_em_2020` and `eleito_2016_reeleito_2020_1t`, both based on CPF links.

**`prefeitos_painel_2016_2020_2024.csv`** (5,569 rows)
- A wide panel: party in 2016, 2020 and 2024; statuses; incumbency flags; 2024 share, margin, runoff flag and number of candidates.
- Known winners: 5,551 in 2016, 5,422 in 2020, 5,531 in 2024 (plus supplementary-election winners in 34 municipalities, 22 of which had no ordinary winner).

---------------------------------------------------------------------------------------------------

## 2. Chamber of Deputies 2022 (target 2): `camara_2022_kalebefukuda/`

**`json/{uf}-c0006.json`** (27 files)
- **URLs:** `https://raw.githubusercontent.com/kalebefukuda/brazil-election-results-2026/main/public/historico/2022/546/{uf}-c0006.json` for uf in ac…to.
- **Repo:** https://github.com/kalebefukuda/brazil-election-results-2026. Its `scripts/historico.mjs` converts the TSE `votacao_candidato_munzona_2022` and `detalhe_votacao_munzona_2022` files into the TSE results-JSON layout.
- **Contents:** for each state, the federal-deputy candidates with valid nominal votes, party, federation and elected status, plus state totals (valid votes including party-label votes, blank and null votes, turnout). The state totalization dates are 05–22/09/2026, so the files reflect the current TSE re-totalized result.

**`json/2022_{uf}-c0005.json` and `json/2018_{uf}-c0005.json`**
- Senate results from the same repo (paths `/2022/546/` and `/2018/297/`). They are used only to find the parties of amendment authors.

**`camara_2022_partido_uf.csv`** (party × state), **`camara_2022_partido_nacional.csv`** and **`camara_2022_totais_uf.csv`**
- Built by `_scripts/build_camara2022.py`.
- Seats total 513, and every state's seat count matches its number of places.
- Nationally: 105.0 M valid nominal votes; 109.3 M total valid votes including party-label votes.

**`camara_2022_nacional_wikipedia_en.csv`**
- Election-night seats and vote % by party or federation: PL 99, FE Brasil 81, UNIÃO 59, PP 47, PSD 42, MDB 42, Republicanos 40, and so on.
- Read with WebFetch from https://en.wikipedia.org/wiki/2022_Brazilian_general_election (cached).

**Caveats**
- Party votes in the JSON-derived tables are **nominal votes only**. Party-label (legenda) votes are known only as a state total: `votos_legenda_uf_implicito` = 4.29 M nationally.
- The "eleitos" count reflects the current TSE status after the 2024–25 re-totalizations of leftover seats (sobras). For example, PL 98 instead of 99, PT 69 vs 68, UNIÃO 57 vs 59, PODE 14 vs 12. Use the Wikipedia table for the election-night distribution.

---------------------------------------------------------------------------------------------------

## 3. Parliamentary amendments (target 3), PARTIAL: `emendas_transferegov_tb/`

**`01-programa.csv` … `06-historico-pagamento.csv`**
- **URLs:** `https://raw.githubusercontent.com/Transparencia-Brasil/emendas-parlamentares-transferencias-especiais/main/tasks/transferegov/outputs/{01-programa,02-plano-acao,03-empenho,04-documento-habil,05-ordem-pagamento,06-historico-pagamento}.csv`
- **Repo:** https://github.com/Transparencia-Brasil/emendas-parlamentares-transferencias-especiais (Transparência Brasil, collected from the Transferegov API, "transferências especiais" module)
- **Contents:**
  - `02-plano-acao`: 13,177 action plans for 2025 individual amendments of the transferência especial ("emenda Pix") type. Fields: beneficiary CNPJ, name, UF, `codigo_ibge_municipio`, author name and code, amendment number, policy area, custeio and investimento values, status.
  - `03-empenho`: 13,177 commitments.
  - `04`/`05`/`06`: documents and payment orders.
- **Coverage:** 2025 only (programs 23 and 24). 4,303 municipalities. R$ 8.81 bn planned or committed, of which R$ 8.16 bn goes to municipalities. R$ 6.44 bn of the municipal amount was paid, meaning a bank order (OB) was sent, as of 29/12/2025.

**Derived files** (built by `_scripts/build_emendas.py`)
- **`transferencias_especiais_2025_plano_acao_enriquecido.csv`:** the plans with committed and paid values attached, plus the author's office and party.
- **`transferencias_especiais_2025_por_municipio.csv`:** 4,303 rows by IBGE code with plan, committed and paid values, number of plans, number of authors, and the planned value by author party.
- **`autores_emendas_2025_partido.csv`:** the 502 authors and how each was matched.
- **`parlamentares_eleitos_2018_2022_partido.csv`:** the 513 deputies elected in 2022 and the 81 senators elected in 2018 or 2022, with party at election.

**How author parties were matched**
- The author's name was matched to these elected lists: 406 exact matches, 55 token matches within the main beneficiary UF, 1 resolved by UF, and 40 unmatched (mostly suplentes in office).
- Matched authors account for 91.5% of the value.
- The party is the one at the election (2018 or 2022), not the current one.

**Not covered:** individual "finalística" amendments, bancada and comissão amendments, and years 2019–2024. The national Portal da Transparência amendment file (`EmendasParlamentares.csv`) was not found on GitHub.

---------------------------------------------------------------------------------------------------

## 4. 2024 mayors' profile (target 4): NOT FOUND

No GitHub copy of the TSE `consulta_cand_2024` (gender, age, education, occupation, `ST_REELEICAO`) was found. Repos either gitignore it or hold a single state. Profiles are available only for:
- 2020 winners, from Herrmann (gender, birth date, race, education, occupation);
- 2016 winners, from Pindograma (gender, age, occupation).

---------------------------------------------------------------------------------------------------

## Searched but not usable (for the record)
- **Hugging Face:** `mlkwy/electedBR` (2020/2024 winners) was not used, since Hugging Face is not an allowed host.
- **GitHub Releases** (blocked host): `pmarkun/dados-eleitorais-brasil` (2018–2024 TSE Parquet) and `juliosaulo/como-meus-vizinhos-votam`.
- **CEM-USP:** `EL2024_MU_BRA_CEM.zip` is on a government site.
- **Single-state repos:** `maiconcombatoficial/resultadoeleicao` (SC, 2012–2024) and `tucotuco22/rs` (RS).
- **First-round duplicate:** `danlessa/Brazil-Municipal-Elections-2020` (`data/clean_data.csv.gz`) duplicates marcofaga's 2020 first round and has a misaligned header; not kept.
