# data/raw/education — sources

Collected in October 2026 from open GitHub repositories (government portals could not be reached from
the environment in which the study was produced). These are secondary copies: cite the original producer (INEP or
IBGE) together with the repository.

| File | Content | Original producer | Repository |
|---|---|---|---|
| `dp_stg_inep_qualidade.csv` | IDEB, its targets, SAEB scores and pass rates by municipality, network (state, municipal) and edition, 2015–2025 | INEP | [realdanielelias/dashboard-publico](https://github.com/realdanielelias/dashboard-publico), staging table `stg_inep_qualidade` (the prefix `dp_` was added here) |
| `dp_stg_inep_inse.csv` | INSE socio-economic index and number of SAEB students by municipality and network, 2019 and 2021 | INEP | same repository, `stg_inep_inse` |
| `dp_stg_censo_sinopse.csv` | School Census synopsis by municipality, 2015–2022: enrolments, teachers, classes and schools by stage and network | INEP | same repository, `stg_censo_sinopse` |
| `ibge_pop.rds` | Municipal population, 2000–2025 (counts, Censuses and intercensal estimates) | IBGE | [rfsaldanha/brpop](https://github.com/rfsaldanha/brpop), `inst/extdata/ibge_pop.rds`; identical to `../social/populacao/brpop_ibge_pop.rds` |
| `municipios.csv` | Municipal IBGE codes, names, coordinates, state codes and SIAFI codes | IBGE | [kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros), `csv/municipios.csv` |
| `panel_ideb_municipal.csv` | National IDEB panel of municipal networks (early years of primary school): IDEB, SAEB, pass rates, population, INSE and the mayoral term of each edition | derived | built by `_scripts/build_ideb_panel.py` from the files above (it reproduces this file exactly) |

The IDEB panel covers 5,451 municipal networks and 32,706 municipality-editions (2015–2025).
