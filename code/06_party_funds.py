"""
06_party_funds.py -- the party-finance pillar with real data (day one, before any behavioural response):
 (1) Fundo Partidario and FEFC under the current rules (2025/2024 allocations) and under the LRG rule
     (mayors in office weighted by population governed; quality weights from the simulated scorecard enter later);
 (2) who wins and who loses, and the Chamber seats of winners and losers (can the rule pass?);
 (3) a new party with no mayors (Missao-like) under both rules;
 (4) the party-switching market: how often mayors change party (TSE 2016-2024), and what the rule pays for a switch.
Outputs: output/party_funds.json, tables/T_party_funds.csv
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json, sys
import numpy as np
import pandas as pd
sys.path.insert(0, _ROOT + '/code')
import lrg2_sim as S

DER = _ROOT + '/data/derived'; OUT = _ROOT + '/output'; TAB = _ROOT + '/tables'
RAW = _ROOT + '/data/raw/elections'
b = pd.read_csv(DER + '/municipios_base.csv')
b['party'] = b.party_2024.replace(S.NORM_PARTY).fillna('OUTROS')
FP = S.Calib().fp_total; FE = S.Calib().fefc_total
parties = sorted(set(b.party) | set(S.FP_SHARE_SQ) | set(S.FEFC_SQ_RAW) | {'PSOL', 'NOVO'})
fp_sq = pd.Series({p: S.FP_SHARE_SQ.get(p, 0.0) for p in parties}); fp_sq /= fp_sq.sum()
fe_sq = pd.Series({p: S.FEFC_SQ_RAW.get(p, 0.0) for p in parties}); fe_sq /= fe_sq.sum()
popg = b.groupby('party').pop2024.sum().reindex(parties).fillna(0)
cntg = b.groupby('party').size().reindex(parties).fillna(0)
popg['OUTROS'] = 0; cntg['OUTROS'] = 0
lrg_pop = popg / popg.sum()
lrg_cnt = cntg / cntg.sum()
# Chamber of Deputies: seats by party (2022 election; current names)
cam = pd.read_csv(RAW + '/camara_2022_kalebefukuda/camara_2022_partido_nacional.csv')
cam['party'] = cam.sg_partido.replace(S.NORM_PARTY).replace({'PSDB/CIDADANIA': 'PSDB'})
seats = cam.groupby('party').eleitos.sum().reindex(parties).fillna(0)
votes = cam.groupby('party').share_votos_nominais.sum().reindex(parties).fillna(0)
df = pd.DataFrame({'mayors': cntg, 'pop_governed_mn': popg / 1e6, 'seats_2022': seats, 'votes_2022': votes,
                   'fp_now': fp_sq * FP / 1e6, 'fp_lrg': lrg_pop * FP / 1e6, 'fp_lrg_count': lrg_cnt * FP / 1e6,
                   'fefc_now': fe_sq * FE / 1e6, 'fefc_lrg': (0.5 * fe_sq + 0.5 * lrg_pop) * FE / 1e6})
df['fp_change'] = df.fp_lrg - df.fp_now
df['fefc_change'] = df.fefc_lrg - df.fefc_now
df['annual_change'] = df.fp_change + df.fefc_change / 2          # FEFC every two years
df = df.drop(index='OUTROS').sort_values('fp_now', ascending=False)
df.round(2).to_csv(TAB + '/T_party_funds.csv')
BIG6 = ['PSD', 'MDB', 'PP', 'UNIAO', 'PL', 'REPUBLICANOS']
CENTRAO = BIG6 + ['PODEMOS', 'AVANTE', 'SOLIDARIEDADE', 'PRD', 'AGIR', 'MOBILIZA', 'PMB', 'DC', 'PRTB']
LEFT = ['PT', 'PSB', 'PDT', 'PCDOB', 'PV', 'REDE', 'PSOL']
res = {}
res['shares'] = {g: dict(fp_now=float(df.loc[df.index.isin(L), 'fp_now'].sum() / df.fp_now.sum()),
                         fp_lrg=float(df.loc[df.index.isin(L), 'fp_lrg'].sum() / df.fp_lrg.sum()),
                         fefc_now=float(df.loc[df.index.isin(L), 'fefc_now'].sum() / df.fefc_now.sum()),
                         fefc_lrg=float(df.loc[df.index.isin(L), 'fefc_lrg'].sum() / df.fefc_lrg.sum()),
                         mayors=float(df.loc[df.index.isin(L), 'mayors'].sum() / df.mayors.sum()),
                         seats=float(df.loc[df.index.isin(L), 'seats_2022'].sum() / 513))
                 for g, L in [('big6', BIG6), ('centrao', CENTRAO), ('left', LEFT)]}
gov = b[b.party != 'OUTROS']                     # municipalities with a known 2024 mayor (Brasilia has none)
srt = np.sort(gov.pop2024.values)[::-1]
n_half = int((np.cumsum(srt) < gov.pop2024.sum() / 2).sum() + 1)
res['top_city_weight'] = dict(sao_paulo_share_of_fp=float(gov.loc[gov.cod_ibge == 3550308, 'pop2024'].iloc[0] / gov.pop2024.sum()),
                              capitals_share=float(gov.loc[gov.capital == 1, 'pop2024'].sum() / gov.pop2024.sum()),
                              n_munis_for_half_fund=n_half, n_governed=int(len(gov)),
                              share_of_munis_for_half_fund=float(n_half / len(gov)))
gain = df.annual_change > 0
res['chamber'] = dict(seats_parties_gaining=int(df.loc[gain, 'seats_2022'].sum()), seats_parties_losing=int(df.loc[~gain, 'seats_2022'].sum()),
                      parties_gaining=list(df.index[gain]), parties_losing=list(df.index[~gain & (df.fp_now > 0)]))
# Hirschman-Herfindahl
hh = lambda s: float(((s / s.sum()) ** 2).sum())
res['hhi'] = dict(fp_now=hh(df.fp_now), fp_lrg=hh(df.fp_lrg))
# new party: 3% of Chamber votes and 15 deputies (enough to pass the art. 17 §3 threshold from 2030), no mayors
v, dep = 0.03, 15
res['new_party'] = dict(vote_share=v, deputies=dep, fp_now_mn=float((0.05 / 20 + 0.95 * v) * FP / 1e6), fp_lrg_mn=0.0,
                        fefc_now_mn=float((0.02 / 29 + 0.35 * v + 0.48 * dep / 513) * FE / 1e6),
                        fefc_lrg_mn=float(0.5 * (0.02 / 29 + 0.35 * v + 0.48 * dep / 513) * FE / 1e6),
                        mayors_needed_for_same_fp=float(v * b.pop2024.sum() / b.pop2024.median()),
                        note='Under current rules only parties above the art. 17 §3 threshold receive the FP: 2.5% of valid '
                             'votes (or 13 deputies) in 2026 and 3% (or 15 deputies) from 2030; the party is assumed to pass it.')
# party switching (real): mayors re-elected in 2024 who changed party label since 2020, and open seats
pp = pd.read_csv(RAW + '/derived/prefeitos_painel_2016_2020_2024.csv')
for col in ['partido_2016', 'partido_2020', 'partido_2024']:
    pp[col] = pp[col].replace(S.NORM_PARTY)
re_ = pp[pp.reeleito_2024_proxy == 1]
res['switching'] = dict(reelected_2024=int(len(re_)), switched_label_2020_2024=float((re_.partido_2020 != re_.partido_2024).mean()),
                        open_seats_same_party=float((pp.loc[pp.reeleito_2024_proxy == 0, 'partido_2020'] == pp.loc[pp.reeleito_2024_proxy == 0, 'partido_2024']).mean()),
                        fp_per_mn_inhabitants_lrg=float(FP / b.pop2024.sum() * 1e6))
json.dump(res, open(OUT + '/party_funds.json', 'w'), indent=1, default=float)
pd.set_option('display.width', 200)
print(df.round(1).head(20).to_string())
print(json.dumps(res, indent=1, default=float))
