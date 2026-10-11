"""Build panel_ideb_municipal.csv (national IDEB panel of municipal networks, early years of primary school)
from the INEP files republished by realdanielelias/dashboard-publico and the IBGE population series (rfsaldanha/brpop).
Run from data/raw/education/ (or pass that folder as the first argument). This is the IDEB-panel part of the data
script of an earlier version of the study; it reproduces the file shipped here exactly."""
import sys
from pathlib import Path

import pandas as pd
import pyreadr

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent

pop = list(pyreadr.read_r(D / 'ibge_pop.rds').values())[0]
pop['code_muni'] = pop['code_muni'].astype(int)
pop['year'] = pop['year'].astype(int)
pop22 = pop[pop.year == 2022][['code_muni', 'pop']].rename(columns={'code_muni': 'cod_ibge', 'pop': 'pop2022'})
pop25 = pop[pop.year == 2025][['code_muni', 'pop']].rename(columns={'code_muni': 'cod_ibge', 'pop': 'pop2025'})

q = pd.read_csv(D / 'dp_stg_inep_qualidade.csv')
m = q[q.rede == 'Municipal'].copy()
m = m.rename(columns={'ideb_iniciais': 'ideb', 'saeb_nota_iniciais': 'N', 'rendimento_iniciais': 'P',
                      'saeb_mat_iniciais': 'mat', 'saeb_lp_iniciais': 'lp'})
m = m[['cod_ibge', 'ano', 'ideb', 'N', 'P', 'mat', 'lp']]
m['uf_code'] = m.cod_ibge // 100000
m = m.merge(pop22, on='cod_ibge', how='left').merge(pop25, on='cod_ibge', how='left')

ins = pd.read_csv(D / 'dp_stg_inep_inse.csv')
ins = ins[ins.rede == 'Municipal'].pivot_table(index='cod_ibge', columns='ano', values=['inse_score', 'qtd_alunos_inse'])
ins.columns = [f'{a}_{b}' for a, b in ins.columns]
ins = ins.reset_index()
m = m.merge(ins, on='cod_ibge', how='left')

# Mayoral term to which each IDEB edition belongs (SAEB is applied in October-November of the edition year)
term_of = {2015: '2013-16', 2017: '2017-20', 2019: '2017-20', 2021: '2021-24', 2023: '2021-24', 2025: '2025-28'}
m['term'] = m.ano.map(term_of)
out = Path(sys.argv[2]) if len(sys.argv) > 2 else D / 'panel_ideb_municipal.csv'
m.to_csv(out, index=False)
print('national panel:', m.shape, 'municipalities:', m.cod_ibge.nunique())
