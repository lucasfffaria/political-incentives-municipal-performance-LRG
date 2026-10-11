# Political incentives and municipal performance: Supplementary Material

Ex ante evaluation of the Lei de Responsabilidade Gerencial (LRG) proposed by Partido Missão (2026).

This folder is the Supplementary Material of the article *Political incentives and municipal performance: An ex
ante evaluation of Brazil's proposed Lei de Responsabilidade Gerencial*. It holds the Supplementary Material document,
`LRG_supplementary_material_v7.docx` and `.pdf`, and the code and data that rebuild every number, table and figure of
the article and of that document.

## The Supplementary Material document

The document has eleven sections, which follow the order of the article. Its sections, tables, figures and equations
carry the prefix S followed by the number of the section to which they belong, so that Table S8.4 is the fourth table
of Section S8; those without the prefix are always cited as being of the article.

| Section | Contents | Supports, in the article |
|---|---|---|
| S1. The proposal and its codification | The five pillars and the reform of the federation; the codification used in the simulation (Table S1.1) | Section 2 |
| S2. The analytical model: derivations and propositions | The effort rule, two benchmark mayors and the strength of incentives (equations S2.1 to S2.8); the ten propositions, each with its proof and the place where the article tests it (equations S2.9 to S2.23); the formal versions of these proofs are in `lean/` | Section 3 |
| S3. Data: sources, checks and replication | Data sources (Table S3.1); repositories and checks (Table S3.2); the scripts and what they reproduce (Table S3.3) | Section 4.1 |
| S4. What the indicators measure | The audit of the ten indicators; the decomposition into places, mayors and noise (equation S4.1); reliability; two official sewage measures and population denominators (Figure S4.1) | Sections 4.2 to 4.4 |
| S5. Money and politics today: further results | The fiscal base by size (Table S5.1); the discretionary amendments; the party funds on day one; fiscal viability and the merger exercise (Figure S5.1) | Section 5 |
| S6. Behavioural evidence and calibration | The evidence in full (Table S6.1); voters; Ceará and gaming at the FPM brackets (Figure S6.1); other settings; how the targets are computed; fit and out-of-sample checks (Table S6.2, Figure S6.2) | Section 6 |
| S7. The simulation model | The equations of the microsimulation (S7.1 to S7.4); designs, scenarios and checks; the parameters (Tables S7.1 and S7.2); the chain to the Chamber | Section 7 |
| S8. Additional simulation results | Where bans fall (Figure S8.1); the factorial, Shapley values, channels and incentives (Table S8.1, Figures S8.2 and S8.3); effects by indicator (Tables S8.2 and S8.3); the FPM tranche (Figure S8.4); commissioners; parties and who governs (Figure S8.5); costs (Table S8.4); variants (Table S8.5); a personal bonus as a benchmark (Figure S8.6); the rules behind the assessments of Table 10 | Section 8 |
| S9. Tests of the sanctions, robustness and sensitivity | Deterrence, execution and the intensity of the threat (Tables S9.1 and S9.2); complementarity and implementation (Figure S9.1, Table S9.3); larger behavioural responses (Figures S9.2 and S9.3, Tables S9.4 and S9.5); every scenario family (Table S9.6, Figure S9.4); Sobol indices (Table S9.7, Figure S9.5); the no-sanction counterfactual and the classification for tutelage (Table S9.8) | Section 9 |
| S10. Legal feasibility in detail | The reasoning behind each assessment of Table 9; votes and the proponents' answers | Section 10 |
| S11. Learning whether the law works | Regression to the mean in real data; the design and power of a pilot (Figure S11.1); other routes to evaluation | Section 11.2 |

## Folders

```
LRG_supplementary_material_v7.docx, .pdf
                       the Supplementary Material document
code/                  Python scripts, run in the order below; lrg2_sim.py is the simulation engine and
                       lrgstyle.py the style shared by the figure scripts
data/raw/              copies of official data; each source folder has a SOURCES.md with the origin, URL and checks
data/derived/          municipal dataset and indicator panels built by 01_build_national.py, and the map data
                       of Figure 2 (fig02_map_data.csv)
output/                numbers produced by the scripts (JSON, CSV, NPZ); numbers.json holds every simulated
                       number cited in the text
tables/                CSV versions of the real-data tables
lean/                  Lean 4 project that states and proves the derivations and propositions of Section S2
                       (equations S2.1 to S2.23, propositions P1 to P10) with the Mathlib library; lean/results/
                       keeps the record of the build that checked every proof (see its README)
figures/               written by the figure scripts of code/; not kept in the repository
TSE_raw_data/          official TSE vote files of 2022 and 2026 (about 14 GB); not used by the study and excluded
                       from git by .gitignore
```

## Requirements

Python 3.11 or later with numpy, pandas, scipy, matplotlib, SALib (1.6), statsmodels, linearmodels, rdrobust,
rddensity, rdata, geopandas, pyreadr, pyarrow and pillow (tested with Python 3.13, numpy 2.5, pandas 3.0, scipy 1.18,
matplotlib 3.11, geopandas 1.2). The formal proofs in `lean/` need Lean 4 (installed with `elan`) and Mathlib, both
pinned in that folder; its README explains how to build them.

## Running

The columns of results give the sections, tables and figures of the article and those of the Supplementary Material
that each script reproduces.

| Script | What it does | Article | Supplementary Material | Time |
|---|---|---|---|---|
| `01_build_national.py` | builds `data/derived/` from `data/raw/` | Section 4.1 | Table S3.1 | 1 min |
| `02_indicator_properties.py` | variance decomposition, reliability, validity | Sections 4.2 to 4.4, Tables 2 and 3, Figure 3 | Sections S4.2 to S4.4, Figure S4.1 | 2 min |
| `04_amendments.py` | 2025 transferências especiais: areas, size, alignment | Section 5.1, Figure 4 | Section S5.2 | <1 min |
| `05_federalism.py` | FPM, own taxes, PEC 188 test, mergers, councillors, commissioners' cost | Sections 5.1, 5.3 and 8.4 | Sections S5.1, S5.4 and S8.5, Table S5.1, Figure S5.1 | 1 min |
| `06_party_funds.py` | party funds on day one | Section 5.2, Figure 5 | Section S5.3 | <1 min |
| `16_incumbency.py` | who governed, who could run again and the open seats, 2012 to 2024 (winners linked by tax identifier) | Section 6.1 | Section S6.1 | 3 min |
| `17_incentive_estimates.py` | close races with and without the incumbent (regression discontinuities, nine robustness specifications, bounds on the electoral incentive), panel, electoral returns to performance | Sections 6.1 and 6.2, Table 4, Figure 6 | Sections S6.1 and S6.2, Table S6.1 | 6 min |
| `18_fpm_rd.py` | bunching at the FPM brackets; regression discontinuity on unconditional money | Section 6.3 | Section S6.3, Figure S6.1 | 3 min |
| `19_calibrate.py 120000 [VARIANT]` | Bayesian calibration (sampling-importance-resampling, block likelihood with correlated targets; records the log evidence); variants `wide`, `noCE`, `noRD`, `noEL`, `noFPM`, `trans50`, `indep`, `v3` (without the open-seat target), and the saturation variants `cap2`, `cap8`, `lin` | Sections 6.5 and 9.2 | Sections S6.5, S6.6, S7.6 and S9.3, Tables S6.2, S7.1, S7.2 and S9.5, Figure S6.2 | 1 min each |
| `03_run_designs.py 400 40` | national Monte Carlo over the 400 calibrated draws: status quo, placebo, 2^5 factorial, single changes to the proposal, tranche doses, the tests of the sanctions (no bans, no sanctions, bans threatened but never executed, bans executed but not anticipated, weight of a ban from ×0 to ×8, the same with the sanctions alone), the no-sanction counterfactual check and the personal-bonus benchmark (66 designs; common random numbers; run in parts with a TAG and merged with `03c_merge_v5.py`) | Sections 7 to 9 | Sections S8 and S9 | ~3 h |
| `03_run_designs.py 120 40 DESIGNS TAG SCENARIO [POSTERIOR]` | scenario runs on the first 120 draws (same shocks): implementation complementarity (`iB`, `iC`, `iD`, with the full factorial under `iD`), voters' reward (`eN`, `eH2`, `eH4`), manipulation (`m0`, `m0s`, `mL`, `mH`, `mA`, `mAs`), banned mayors (`lameM`, `iDlameM`), responsiveness of effort (`dm15`, `dm2`, `dm3`), weight of money (`km2`, `km3`), saturation (`cap2`, `cap8`, `lin` with their own posteriors) and the calibration variants (`base` with `output/posterior_draws_VARIANT.npz`, tags `cv_VARIANT`) | Section 9 | Sections S9.2 to S9.5 | ~4 h in all |
| `03c_merge_v5.py` | assembles the main run and the scenario families and checks that every part shares the same draws and shocks | none | none | 1 min |
| `22_scenarios.py` | summarises the scenario runs into `output/scenarios.json` | Section 9, Tables 7 and 8 | Section S9.4, Table S9.6 | <1 min |
| `23_v5_tests.py` | the tests of the sanctions (deterrence against execution, intensity), complementarity, effects by indicator, the plausibility analysis of larger behavioural responses and the technical checks, into `output/v5_tests.json` | Sections 8.2, 9.1 and 9.2 | Sections S8.3, S9.1 to S9.3 and S9.6 | 1 min |
| `07_sobol.py 64` | Sobol sensitivity analysis over the calibrated ranges (17 groups, including implementation complementarity; outputs include the shares of the effect kept without bans and without sanctions and the deterrence of bans; `run PART NPARTS` and `merge NPARTS` split it) | Section 9.3 | Section S9.5, Table S9.7, Figure S9.5 | ~45 min |
| `08_chain.py` | illustrative chain from municipal outcomes to the Chamber vote | Sections 8.5 and 10.1 | Section S7.7 | <1 min |
| `09_rtm.py` | regression to the mean in real data | Section 11.2 | Section S11.1 | <1 min |
| `20_pilot_power.py` | minimum detectable effects of a factorial pilot | Section 11.2 | Section S11.2, Figure S11.1 | <1 min |
| `10_figures_data.py` | figures from real data | Figures 2 to 5 | Figures S4.1 and S5.1 | 2 min |
| `21_figures_behaviour.py` | figures from the incentive estimates and the calibration | Figure 6 | Figures S6.1 and S6.2 | <1 min |
| `13_numbers.py` | collects every simulated number into `output/numbers.json` (with the scenarios, the calibration variants and the tests) | all | all | <1 min |
| `15_verdict.py` | assessment of each causal link | Table 10, Figure 13 | Section S8.10 | <1 min |
| `11_figures_diagrams.py` | theory-of-change diagrams | Figures 1 and 13 | none | <1 min |
| `12_figures_sim.py` | figures from the simulation | Figures 7 to 12 | Figures S8.1 to S8.6, S9.1 to S9.5 and S11.1 | 2 min |
| `lean/`: `lake exe cache get`, then `lake build` | formal proofs of the derivations and propositions of the model, checked by machine (Lean 4 and Mathlib) | Sections 3.3 and 3.5 | Section S2 | a few minutes, after a 5 GB download |

The four figure scripts of `code/` compute the values that each figure plots.

Scripts read and write paths relative to the repository root (or to the directory in the environment variable
`LRG_ROOT`). All random draws are seeded, so results reproduce exactly. `output/` also keeps the partial runs that
`03c_merge_v5.py` assembles (`designs_metrics_v4full.npz`, `designs_metrics_v5A.npz` and `designs_metrics_v5B.npz`,
with their summaries, `v4_families/` and `v5_parts/`), so that the merge can be re-run and checked.

## Data

Every raw file is a copy of official data published in an open repository (mostly GitHub), checked against official
national totals. The `SOURCES.md` file in each folder of `data/raw/` gives the repository, the download URL, the
original producer (IBGE, INEP, RAIS/MTE, MDS, SNIS, IPEA/SIM, STN/SICONFI, TSE, Transferegov) and the checks; Tables
S3.1 and S3.2 of the Supplementary Material summarise them. Folder and file names inside `data/raw/` keep the names
of the source products and repositories (for example PIB dos Municípios, RAIS, SICONFI), so that each file can be
traced to its source; the code reads them under these names.

Every raw file is included except one: `data/raw/elections/pindograma_2016/prefeitos_longevos.Rdata` (21.7 MB), which
holds candidates' names and tax identifiers (CPF). It is used only to link mayors across elections
(`16_incumbency.py` and `data/raw/elections/_scripts/build_mayors.py`) and is not redistributed here; download it from
the URL in `data/raw/elections/SOURCES.md`. Its products are included: `data/raw/elections/derived/`, which keeps
candidates' names as published in the official results but no tax identifiers, and
`data/derived/incumbency_2012_2024.csv`, which has neither; everything else runs on what is included. The
largest file is the SNIS water-and-sewage table (59 MB).

Known limitations: SICONFI revenue data cover 3,243 municipalities in 2024 (the rest are imputed; Section 5.3 of the
article and Section S5.4 of the Supplementary Material); the homicide panel covers 1996 to 2016 plus 2022 rates;
literacy (ICA) has two editions (2023 and 2024); robberies, favelas and waiting times have no annual municipal series,
and care for aggression against women produces counts too small to use; none of the four is simulated.
