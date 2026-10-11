"""
16_incumbency.py -- who governed each municipality, whether the mayor could run again, and how close the
re-election races were (2012-2024). Builds data/derived/incumbency_2012_2024.csv, used by the estimations of
how mayors respond to incentives (17_incentive_estimates.py).

Sources (data/raw/elections, see SOURCES.md):
  pindograma_2016/prefeitos_longevos.Rdata  winners 2012 and 2016 with CPF; 2020 mayoral candidates with CPF
  marcofaga_2020/prefeito2020.csv            2020 first-round votes by candidate (ballot names)
  derived/prefeitos_2020_municipio_1turno.csv 2020 winners (CPF link to 2016 winner)
  derived/prefeito_2024_candidatos_municipio.csv 2024 votes by candidate (TSE)
Personal identifiers (CPF, names) are used only to link records and are not written to the output.
v4 adds the open seats of 2020 (the 2016 winner did not run): the margin of the outgoing mayor's 2016 party (and coalition),
and, where the incumbent lost, whether the ruling party changed.
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import re, unicodedata, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')
E = _ROOT + '/data/raw/elections'
OUT = _ROOT + '/data/derived'


def norm(s):
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ''
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    s = s.upper().replace('-', ' ').replace("'", ' ').replace('.', ' ')
    return re.sub(r'\s+', ' ', s).strip()


# ------------------------------------------------------------------ municipality keys
xw = pd.read_csv(E + '/crosswalk/municipios_tse_ibge_2024.csv', dtype={'codigo_tse': int, 'codigo_ibge': int})
xw['nkey'] = xw.uf + '|' + xw.nome_municipio.map(norm)
k2c = dict(zip(xw.nkey, xw.codigo_tse))
tse2ibge = dict(zip(xw.codigo_tse, xw.codigo_ibge))
m20 = pd.read_csv(E + '/marcofaga_2020/prefeito2020.csv', sep=';', dtype=str)
for uf, nm, cd in zip(m20.uf, m20.nomemun, m20.codtse):
    k2c.setdefault(uf + '|' + norm(nm), int(cd))
c24 = pd.read_csv(E + '/derived/prefeito_2024_candidatos_municipio.csv', dtype={'CD_MUNICIPIO': int})
for uf, nm, cd in zip(c24.SG_UF, c24.NM_MUNICIPIO, c24.CD_MUNICIPIO):
    k2c.setdefault(uf + '|' + norm(nm), cd)

import rdata
conv = rdata.read_rda(E + '/pindograma_2016/prefeitos_longevos.Rdata', default_encoding='utf8')
P = conv['prefeitos'].copy()
P['cd'] = (P.UF + '|' + P.MUNICIPIO.map(norm)).map(k2c)
cand20 = conv['candidatos'].copy()
cand20['cd'] = (cand20.UF + '|' + cand20.MUNICIPIO.map(norm)).map(k2c)


def winners(year):
    w = P[(P.ANO_ELEICAO == year) & P.cd.notna()].copy()
    n = w.groupby('cd').size()
    w = w[w.cd.map(n) == 1]                      # drop municipalities with two winners (supplementary elections)
    return w.set_index(w.cd.astype(int))


# all winners 1996-2016, including supplementary elections ('prefeitos' keeps one record per person)
PD = conv['prefeitos_dup'].copy()
PD['cd'] = (PD.UF + '|' + PD.MUNICIPIO.map(norm)).map(k2c)
PD = PD[PD.cd.notna()]; PD['cd'] = PD.cd.astype(int)


def cpf_sets(year):
    return PD[PD.ANO_ELEICAO == year].groupby('cd').CPF.apply(set).to_dict()


w16 = winners(2016)
cs08, cs12 = cpf_sets(2008), cpf_sets(2012)
df = pd.DataFrame(index=sorted(set(xw.codigo_tse)))
df.index.name = 'cd_tse'
df['cod_ibge'] = df.index.map(tse2ibge)
df['uf'] = df.index.map(dict(zip(xw.codigo_tse, xw.uf)))
df['has_2016'] = df.index.isin(w16.index)
cpf16 = w16.CPF.to_dict()
# a mayor elected for a second consecutive mandate cannot run again: 2013-16 (2012 winner had won in 2008)
# and 2017-20 (2016 winner had won in 2012, including supplementary elections)
cs12_one = PD[PD.ANO_ELEICAO == 2012].groupby('cd').CPF.apply(list).to_dict()
df['lame_2013'] = [float(len(set(cs12_one[i])) == 1 and next(iter(cs12_one[i])) in cs08[i]) if (i in cs12_one and i in cs08) else np.nan
                   for i in df.index]
df['lame_2017'] = [float(cpf16[i] in cs12[i]) if (i in cpf16 and i in cs12) else np.nan for i in df.index]

# ------------------------------------------------------------------ 2020: did the 2016 winner run, and with what margin?
# party names harmonised to 2020 (mergers and renamings between 2016 and 2020)
PMAP = {'PMDB': 'MDB', 'PRB': 'REPUBLICANOS', 'PR': 'PL', 'PPS': 'CIDADANIA', 'PTN': 'PODE', 'PHS': 'PODE', 'PEN': 'PATRIOTA',
        'PRP': 'PATRIOTA', 'PATRI': 'PATRIOTA', 'PT do B': 'AVANTE', 'PTdoB': 'AVANTE', 'SD': 'SOLIDARIEDADE', 'PSDC': 'DC',
        'PPL': 'PCdoB', 'PC do B': 'PCdoB'}
m20['cd'] = m20.codtse.astype(int)
m20['share'] = pd.to_numeric(m20.votosporc.str.replace(',', '.'), errors='coerce')
m20['votes'] = pd.to_numeric(m20.votosabs, errors='coerce')
m20['nk'] = m20.nomeurna.map(norm)
cand20 = cand20[cand20.cd.notna()].copy(); cand20['cd'] = cand20.cd.astype(int)
cand20['nk'] = cand20.NOME_URNA.map(norm)
inc20 = {}
for cd, g in cand20.groupby('cd'):
    if cd in cpf16:
        hit = g[g.CPF == cpf16[cd]]
        if len(hit):
            inc20[cd] = hit.nk.iloc[0]
df['inc_ran_2020'] = [float(i in inc20) if i in cpf16 else np.nan for i in df.index]
rows = []
for cd, g in m20.groupby('cd'):
    g = g[g.share.notna()]
    tot = g.votes.sum()
    second = (g.situacao == '2O TURNO').any()
    decided = (g.situacao == 'ELEITO').any()
    r = dict(cd_tse=cd, round2_2020=second, decided_2020=decided, n_cand_2020=len(g))
    if cd in inc20 and len(g) >= 1:
        me = g[g.nk == inc20[cd]]
        if len(me) == 0:                          # ballot name changed: try a token match
            toks = set(inc20[cd].split())
            sc = g.nk.map(lambda s: len(toks & set(s.split())) / max(len(toks), 1))
            if sc.max() >= 0.5 and (sc == sc.max()).sum() == 1:
                me = g[sc == sc.max()]
        if len(me) == 1:
            s_inc = 100 * me.votes.iloc[0] / tot if tot > 0 else np.nan
            others = g.drop(me.index)
            s_opp = 100 * others.votes.max() / tot if (tot > 0 and len(others)) else 0.0
            r.update(inc_share_2020=s_inc, opp_share_2020=s_opp, margin_2020=s_inc - s_opp,
                     inc_status_2020=me.situacao.iloc[0])
            # v4: where the incumbent lost, did the ruling party change? (the winner's party against the incumbent's 2020 party)
            if me.situacao.iloc[0] != 'ELEITO' and len(others):
                wn = others[others.situacao == 'ELEITO']
                if len(wn) == 1:
                    r['party_change_if_lost_2020'] = float(PMAP.get(wn.partido.iloc[0], wn.partido.iloc[0]) !=
                                                           PMAP.get(me.partido.iloc[0], me.partido.iloc[0]))
    rows.append(r)
r20 = pd.DataFrame(rows).set_index('cd_tse')
df = df.join(r20)

# ------------------------------------------------------------------ v4: open seats in 2020 (the 2016 winner did not run): party continuity
# margin = first-round share of the best candidate of the outgoing mayor's 2016 party minus the best other candidate's share;
# an alternative counts any party of the outgoing mayor's 2016 coalition as continuity
e16 = pd.read_csv(E + '/derived/prefeitos_2016_eleitos.csv').drop_duplicates('cd_municipio_tse').set_index('cd_municipio_tse')
party16 = e16.eleito_sg_partido_recodificado.map(lambda p: PMAP.get(p, p))
coal16 = e16.eleito_coligacao.fillna('').map(lambda s_: {PMAP.get(x.strip(), x.strip()) for x in s_.split('/') if x.strip()})
m20['pn'] = m20.partido.map(lambda p: PMAP.get(p, p))
rows = []
for cd, g in m20.groupby('cd'):
    g = g[g.share.notna()]
    tot = g.votes.sum()
    if cd not in party16.index or tot <= 0 or len(g) < 2:
        continue
    p16 = party16[cd]
    r = dict(cd_tse=cd)
    own, oth = g[g.pn == p16], g[g.pn != p16]
    if len(own) and len(oth):
        r['margin_party_2020'] = 100 * (own.votes.max() - oth.votes.max()) / tot
    cs = coal16.get(cd, set()) | {p16}
    ownc, othc = g[g.pn.isin(cs)], g[~g.pn.isin(cs)]
    if len(ownc) and len(othc):
        r['margin_coal_2020'] = 100 * (ownc.votes.max() - othc.votes.max()) / tot
    rows.append(r)
ro = pd.DataFrame(rows).set_index('cd_tse')
df = df.join(ro)
d20 = pd.read_csv(E + '/derived/prefeitos_2020_municipio_1turno.csv')
d20 = d20.set_index('cd_municipio_tse')
df['lame_2021'] = df.index.map(d20.eleito_2020_igual_eleito_2016_cpf)     # 2020 winner = 2016 winner (by CPF)

# ------------------------------------------------------------------ 2024: did the (first-term) 2020 winner run, and win?
cpf20 = {}
for cd, nk in zip(d20.index, d20.eleito_nm_urna.map(norm)):
    g = cand20[(cand20.cd == cd) & (cand20.nk == nk)]
    if len(g) == 1:
        cpf20[cd] = (g.CANDIDATO.iloc[0], g.NOME_URNA.iloc[0])
o24 = c24[c24.DS_ELEICAO == 'ELEIÇÕES MUNICIPAIS 2024'].copy()
o24['nk'] = o24.NM_CANDIDATO.map(norm); o24['nu'] = o24.NM_URNA_CANDIDATO.map(norm)
rows = []
for cd, g in o24.groupby('CD_MUNICIPIO'):
    r = dict(cd_tse=cd, round2_2024=(g.NR_TURNO == 2).any())
    g1 = g[g.NR_TURNO == 1]
    tot = g1.votos_validos.sum()
    if cd in cpf20:
        full, urna = cpf20[cd]
        me = g1[g1.nk == norm(full)]
        if len(me) == 0:
            me = g1[g1.nu == norm(urna)]
        r['inc20_ran_2024'] = float(len(me) == 1)
        if len(me) == 1 and tot > 0:
            s_inc = 100 * me.votos_validos.iloc[0] / tot
            s_opp = 100 * g1.drop(me.index).votos_validos.max() / tot if len(g1) > 1 else 0.0
            won = me.DS_SIT_TOT_TURNO.iloc[0] == 'ELEITO'
            if (g.NR_TURNO == 2).any():
                g2 = g[(g.NR_TURNO == 2)]
                me2 = g2[g2.SQ_CANDIDATO == me.SQ_CANDIDATO.iloc[0]]
                won = len(me2) == 1 and me2.DS_SIT_TOT_TURNO.iloc[0] == 'ELEITO'
            r.update(inc_share_2024=s_inc, opp_share_2024=s_opp, margin_2024=s_inc - s_opp, inc_won_2024=float(won))
    rows.append(r)
r24 = pd.DataFrame(rows).set_index('cd_tse')
df = df.join(r24)
df.loc[df.lame_2021 == 1, 'inc20_ran_2024'] = np.nan       # term-limited in 2024
df['inc_won_2020'] = np.where(df.margin_2020.notna(), (df.margin_2020 > 0).astype(float), np.nan)
df.reset_index().to_csv(OUT + '/incumbency_2012_2024.csv', index=False)

print('municipalities', len(df))
print('lame duck 2013-16:', int(np.nansum(df.lame_2013)), 'of', int(df.lame_2013.notna().sum()),
      ' lame duck 2017-20:', int(np.nansum(df.lame_2017)), 'of', int(df.lame_2017.notna().sum()))
print('2016 winner ran in 2020:', int(np.nansum(df.inc_ran_2020)), 'of', int(df.inc_ran_2020.notna().sum()))
print('  with 2020 margin:', int(df.margin_2020.notna().sum()), ' won:', int(np.nansum(df.inc_won_2020)),
      ' second round:', int(df.round2_2020.fillna(False).sum()))
print('  |margin| < 5 pp:', int((df.margin_2020.abs() < 5).sum()), ' < 10 pp:', int((df.margin_2020.abs() < 10).sum()))
print('lame duck 2021-24:', int(np.nansum(df.lame_2021)), 'of', int(df.lame_2021.notna().sum()))
print('2020 winner (first term) ran in 2024:', int(np.nansum(df.inc20_ran_2024)), 'of', int(df.inc20_ran_2024.notna().sum()),
      ' won:', int(np.nansum(df.inc_won_2024)))
op = df[(df.inc_ran_2020 == 0) & ~df.round2_2020.fillna(False).astype(bool)]
print('open seats 2020 (2016 winner did not run), first round:', len(op), ' with a candidate of the outgoing party:',
      int(op.margin_party_2020.notna().sum()), ' |margin| < 10 pp:', int((op.margin_party_2020.abs() < 10).sum()),
      ' party kept:', int((op.margin_party_2020 > 0).sum()))
cl = df[(df.margin_2020.abs() < 10) & (df.margin_2020 < 0)]
print('incumbent lost by < 10 pp: ruling party changed in', round(float(cl.party_change_if_lost_2020.mean()), 3), 'of', int(cl.party_change_if_lost_2020.notna().sum()))
chk = df[df.margin_2020.notna()]
print('consistency: margin>0 vs 2020 winner = 2016 winner:', pd.crosstab(chk.margin_2020 > 0, chk.lame_2021).to_string())
