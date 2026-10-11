"""Build municipality-level mayor tables (2016, 2020, 2024) from the raw files
saved under data/raw/elections. Run with: python3 -I build_mayors.py <elections_dir>
"""
import sys, os, re, unicodedata, warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")
E = sys.argv[1]
OUT = os.path.join(E, "derived")
os.makedirs(OUT, exist_ok=True)


def norm(s):
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.upper().replace("-", " ").replace("'", " ").replace(".", " ")
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- crosswalk
xw = pd.read_csv(os.path.join(E, "crosswalk", "municipios_brasileiros_tse.csv"),
                 dtype={"codigo_tse": int, "codigo_ibge": int})
extra = pd.DataFrame([{"codigo_tse": 73709, "uf": "MT", "nome_municipio": "BOA ESPERANÇA DO NORTE",
                       "capital": 0, "codigo_ibge": 5101837}])
xw = pd.concat([xw, extra], ignore_index=True)
xw.to_csv(os.path.join(E, "crosswalk", "municipios_tse_ibge_2024.csv"), index=False)
xw["nkey"] = xw.uf + "|" + xw.nome_municipio.map(norm)
tse2ibge = dict(zip(xw.codigo_tse, xw.codigo_ibge))

# ---------------------------------------------------------------- 2024 (TSE)
d = pd.read_parquet(os.path.join(E, "tse_2024_votacao_pedrovitorsilva",
                                 "votacao_candidato_munzona_2024_brasil.parquet"))
p = d[d.CD_CARGO == 11].copy()
keys = ["CD_ELEICAO", "DS_ELEICAO", "DT_ELEICAO", "NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO",
        "SQ_CANDIDATO", "NR_CANDIDATO", "NM_CANDIDATO", "NM_URNA_CANDIDATO", "NR_PARTIDO", "SG_PARTIDO",
        "TP_AGREMIACAO", "SG_FEDERACAO", "DS_COMPOSICAO_COLIGACAO", "DS_SIT_TOT_TURNO",
        "DS_SITUACAO_CASSACAO", "DS_SITUACAO_JULGAMENTO"]
for k in keys:
    p[k] = p[k].fillna("")
c = (p.groupby(keys, dropna=False)
       .agg(votos_nominais=("QT_VOTOS_NOMINAIS", "sum"),
            votos_validos=("QT_VOTOS_NOMINAIS_VALIDOS", "sum"),
            destino=("NM_TIPO_DESTINACAO_VOTOS", lambda s: "/".join(sorted(set(s)))))
       .reset_index())
c.to_csv(os.path.join(OUT, "prefeito_2024_candidatos_municipio.csv"), index=False)

ordm = c[c.DS_ELEICAO == "ELEIÇÕES MUNICIPAIS 2024"]
r1 = ordm[ordm.NR_TURNO == 1]
r2 = ordm[ordm.NR_TURNO == 2]
tot1 = r1.groupby("CD_MUNICIPIO").votos_validos.sum().rename("votos_validos_1t")
tot2 = r2.groupby("CD_MUNICIPIO").votos_validos.sum().rename("votos_validos_2t")
ncand = r1.groupby("CD_MUNICIPIO").SQ_CANDIDATO.nunique().rename("n_candidatos_1t")
ncand_v = r1[r1.destino.str.contains("Válido")].groupby("CD_MUNICIPIO").SQ_CANDIDATO.nunique().rename("n_candidatos_com_votos_validos_1t")
base = (ordm[["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO"]].drop_duplicates("CD_MUNICIPIO")
        .set_index("CD_MUNICIPIO").join([ncand, ncand_v, tot1, tot2]))
base["segundo_turno"] = base.index.isin(r2.CD_MUNICIPIO).astype(int)
base["primeiro_turno_ausente_no_arquivo"] = (~base.index.isin(r1.CD_MUNICIPIO)).astype(int)

el = ordm[ordm.DS_SIT_TOT_TURNO == "ELEITO"].sort_values("NR_TURNO").drop_duplicates("CD_MUNICIPIO", keep="last")
el = el.set_index("CD_MUNICIPIO")
w = pd.DataFrame(index=el.index)
w["eleito_turno"] = el.NR_TURNO
for a, b in [("eleito_sq_candidato", "SQ_CANDIDATO"), ("eleito_nr_candidato", "NR_CANDIDATO"),
             ("eleito_nm_candidato", "NM_CANDIDATO"), ("eleito_nm_urna", "NM_URNA_CANDIDATO"),
             ("eleito_nr_partido", "NR_PARTIDO"), ("eleito_sg_partido", "SG_PARTIDO"),
             ("eleito_tp_agremiacao", "TP_AGREMIACAO"), ("eleito_sg_federacao", "SG_FEDERACAO"),
             ("eleito_coligacao", "DS_COMPOSICAO_COLIGACAO"), ("eleito_situacao_cassacao", "DS_SITUACAO_CASSACAO")]:
    w[a] = el[b]
# winner votes in round 1 and final round
v1 = r1.set_index(["CD_MUNICIPIO", "SQ_CANDIDATO"]).votos_validos
v2 = r2.set_index(["CD_MUNICIPIO", "SQ_CANDIDATO"]).votos_validos
w["eleito_votos_1t"] = [v1.get((m, s), np.nan) for m, s in zip(w.index, w.eleito_sq_candidato)]
w["eleito_votos_2t"] = [v2.get((m, s), np.nan) if t == 2 else np.nan
                        for m, s, t in zip(w.index, w.eleito_sq_candidato, w.eleito_turno)]
base = base.join(w)
base["eleito_share_1t"] = base.eleito_votos_1t / base.votos_validos_1t
base["eleito_share_2t"] = base.eleito_votos_2t / base.votos_validos_2t
base["eleito_share_final"] = np.where(base.eleito_turno == 2, base.eleito_share_2t, base.eleito_share_1t)


# runner-up in the deciding round (round 2 if it happened, else round 1)
def runner_up(df, tot):
    df = df.sort_values(["CD_MUNICIPIO", "votos_validos"], ascending=[True, False])
    df = df[df.DS_SIT_TOT_TURNO != "ELEITO"]
    ru = df.drop_duplicates("CD_MUNICIPIO").set_index("CD_MUNICIPIO")
    out = pd.DataFrame({"segundo_nm_urna": ru.NM_URNA_CANDIDATO, "segundo_sg_partido": ru.SG_PARTIDO,
                        "segundo_votos": ru.votos_validos})
    out["segundo_share"] = out.segundo_votos / tot.reindex(out.index)
    return out


ru1 = runner_up(r1, tot1)
ru2 = runner_up(r2, tot2)
ru = pd.concat([ru1[~ru1.index.isin(ru2.index)], ru2])
base = base.join(ru)
base["margem_final"] = base.eleito_share_final - base.segundo_share
base.loc[base.eleito_turno.isna(), ["segundo_nm_urna", "segundo_sg_partido", "segundo_votos", "segundo_share", "margem_final"]] = np.nan

# supplementary elections (after the ordinary one)
sup = c[c.DS_ELEICAO != "ELEIÇÕES MUNICIPAIS 2024"]
if len(sup):
    sup = sup.assign(dt=pd.to_datetime(sup.DT_ELEICAO, format="%d/%m/%Y"))
    nsup = sup.groupby("CD_MUNICIPIO").CD_ELEICAO.nunique().rename("n_eleicoes_suplementares_prefeito")
    sel = sup[sup.DS_SIT_TOT_TURNO == "ELEITO"].sort_values("dt").drop_duplicates("CD_MUNICIPIO", keep="last").set_index("CD_MUNICIPIO")
    s2 = pd.DataFrame({"suplementar_ultima_data": sel.DT_ELEICAO, "suplementar_ds_eleicao": sel.DS_ELEICAO,
                       "suplementar_eleito_nm_urna": sel.NM_URNA_CANDIDATO,
                       "suplementar_eleito_sg_partido": sel.SG_PARTIDO})
    base = base.join(nsup).join(s2)
base["n_eleicoes_suplementares_prefeito"] = base.n_eleicoes_suplementares_prefeito.fillna(0).astype(int)
base["status_2024"] = np.where(base.eleito_sg_partido.notna(), "eleito_na_ordinaria", "sem_eleito_na_ordinaria")
base = base.reset_index().rename(columns={"CD_MUNICIPIO": "cd_municipio_tse", "SG_UF": "sg_uf", "NM_MUNICIPIO": "nm_municipio"})

# municipalities expected but absent from the TSE file
present = set(base.cd_municipio_tse)
miss = xw[(~xw.codigo_tse.isin(present)) & (xw.uf != "DF") & (xw.codigo_tse != 30015)]
miss_rows = pd.DataFrame({"cd_municipio_tse": miss.codigo_tse, "sg_uf": miss.uf, "nm_municipio": miss.nome_municipio,
                          "status_2024": "ausente_no_arquivo_tse", "segundo_turno": np.nan,
                          "n_eleicoes_suplementares_prefeito": 0})
base = pd.concat([base, miss_rows], ignore_index=True)
base.insert(1, "cd_municipio_ibge", base.cd_municipio_tse.map(tse2ibge))
base.insert(0, "ano", 2024)

# ---------------------------------------------------------------- 2020 (marcofaga, 1st round)
m = pd.read_csv(os.path.join(E, "marcofaga_2020", "prefeito2020.csv"), sep=";", dtype=str)
m["votos"] = m.votosabs.astype(int)
m["pct_tse"] = m.votosporc.str.replace(",", ".").astype(float)
m["cd_tse"] = m.codtse.astype(int)
g20 = m.groupby("cd_tse")
b20 = pd.DataFrame({
    "sg_uf": g20.uf.first(), "nm_municipio": g20.nomemun.first(), "cd_municipio_ibge": g20.codibge.first().astype(int),
    "n_candidatos_1t": g20.size(), "votos_candidatos_1t": g20.votos.sum(),
    "apuracao_pct": g20.apuracao.first(), "hora_divulgacao": g20.hora.first(),
})
b20["segundo_turno"] = g20.situacao.apply(lambda s: int((s == "2O TURNO").any()))
e20 = m[m.situacao == "ELEITO"].set_index("cd_tse")
b20 = b20.join(pd.DataFrame({"eleito_nm_urna": e20.nomeurna, "eleito_nr_candidato": e20.ncand,
                             "eleito_sg_partido": e20.partido, "eleito_votos_1t": e20.votos,
                             "eleito_share_1t_tse": e20.pct_tse / 100}))
# runner-up / 2nd-round contenders
srt = m.sort_values(["cd_tse", "votos"], ascending=[True, False])
top = srt.groupby("cd_tse").head(2)
t1 = top.groupby("cd_tse").nth(0).set_index("cd_tse")
t2 = top.groupby("cd_tse").nth(1).set_index("cd_tse")
b20["primeiro_1t_nm_urna"] = t1.nomeurna; b20["primeiro_1t_sg_partido"] = t1.partido; b20["primeiro_1t_share_tse"] = t1.pct_tse / 100
b20["segundo_1t_nm_urna"] = t2.nomeurna; b20["segundo_1t_sg_partido"] = t2.partido; b20["segundo_1t_share_tse"] = t2.pct_tse / 100
b20["margem_1t"] = np.where(b20.eleito_sg_partido.notna(), b20.primeiro_1t_share_tse - b20.segundo_1t_share_tse, np.nan)
b20["status_2020"] = np.select([b20.eleito_sg_partido.notna(), b20.segundo_turno == 1],
                               ["eleito_no_1t", "segundo_turno_resultado_ausente"], "indefinido_na_divulgacao_1t")
# Herrmann: incumbency flag + profile of the winner
h = pd.read_csv(os.path.join(E, "herrmann_2020", "planos-de-governo.csv"), dtype=str)
h["cd_tse"] = h.codigo_cidade_tse.astype(int)
h["nk"] = h.nome_urna.map(norm)
h["pk"] = h.sigla_partido.fillna("").str.replace(" ", "").str.upper()
h = h.drop_duplicates(["cd_tse", "nk", "pk"])
e20r = e20.reset_index()
e20r["nk"] = e20r.nomeurna.map(norm)
e20r["pk"] = e20r.partido.fillna("").str.replace(" ", "").str.upper()
# 1) municipality + ballot name, when the ballot name is unique in the municipality
hu = h.groupby(["cd_tse", "nk"]).filter(lambda x: len(x) == 1)
j1 = e20r.merge(hu.drop(columns=["pk"]), on=["cd_tse", "nk"], how="inner")
# 2) municipality + ballot name + party
rest = e20r[~e20r.cd_tse.isin(j1.cd_tse)]
j2 = rest.merge(h, on=["cd_tse", "nk", "pk"], how="inner")
# 3) municipality + party, when the party has a single candidate there
rest = rest[~rest.cd_tse.isin(j2.cd_tse)]
hp = h[h.pk != ""].groupby(["cd_tse", "pk"]).filter(lambda x: len(x) == 1)
j3 = rest.merge(hp.drop(columns=["nk"]), on=["cd_tse", "pk"], how="inner")
j = pd.concat([j1.assign(match="nome_urna"), j2.assign(match="nome_urna+partido"), j3.assign(match="partido")],
              ignore_index=True)
j = j.drop_duplicates("cd_tse").set_index("cd_tse")
prof = pd.DataFrame({"eleito_sq_candidato": j.codigo_candidato, "eleito_candidato_reeleicao": j.candidato_reeleicao,
                     "eleito_genero": j.genero, "eleito_data_nascimento": j.data_nascimento, "eleito_cor_raca": j.cor_raca,
                     "eleito_grau_instrucao": j.grau_instrucao, "eleito_ocupacao": j.ocupacao,
                     "herrmann_match": j.match})
b20 = b20.join(prof)
inc = h[h.candidato_reeleicao == "S"].groupby("cd_tse").size().rename("n_incumbentes_concorrendo")
b20 = b20.join(inc)
b20["n_incumbentes_concorrendo"] = b20.n_incumbentes_concorrendo.fillna(0).astype(int)
b20 = b20.reset_index().rename(columns={"cd_tse": "cd_municipio_tse"})
b20.insert(0, "ano", 2020)

# ---------------------------------------------------------------- 2016 (pindograma)
import rdata
conv = rdata.read_rda(os.path.join(E, "pindograma_2016", "prefeitos_longevos.Rdata"), default_encoding="utf8")
p16 = conv["prefeitos"]
p16 = p16[p16.ANO_ELEICAO == 2016].copy()
cand20 = conv["candidatos"].copy()
p16["nkey"] = p16.UF + "|" + p16.MUNICIPIO.map(norm)
k2c = dict(zip(xw.nkey, xw.codigo_tse))
# extra name keys from TSE 2020 and 2024 files
for uf, nm, cd in zip(m.uf, m.nomemun, m.cd_tse):
    k2c.setdefault(uf + "|" + norm(nm), cd)
for uf, nm, cd in zip(r1.SG_UF, r1.NM_MUNICIPIO, r1.CD_MUNICIPIO):
    k2c.setdefault(uf + "|" + norm(nm), cd)
p16["cd_municipio_tse"] = p16.nkey.map(k2c)
unm = p16[p16.cd_municipio_tse.isna()][["UF", "MUNICIPIO"]].drop_duplicates()
print("2016 unmatched municipality names:", len(unm)); print(unm.to_string())
p16["n_registros_municipio"] = p16.groupby("nkey").nkey.transform("size")
o16 = pd.DataFrame({
    "ano": 2016, "cd_municipio_tse": p16.cd_municipio_tse, "sg_uf": p16.UF, "nm_municipio": p16.MUNICIPIO,
    "eleito_nm_candidato": p16.CANDIDATO, "eleito_nm_urna": p16.NOME_URNA, "eleito_sg_partido_recodificado": p16.PARTIDO,
    "eleito_coligacao": p16.COMPOSICAO_LEGENDA, "eleito_ocupacao": p16.OCUPACAO, "eleito_genero": p16.SEXO,
    "eleito_idade": p16.IDADE.where(p16.IDADE.between(18, 110)), "n_registros_municipio": p16.n_registros_municipio,
    "_cpf": p16.CPF})
o16.insert(2, "cd_municipio_ibge", o16.cd_municipio_tse.map(tse2ibge))

# 2016 winner ran / re-elected in 2020 (CPF link through pindograma 2020 candidate list)
cand20["nkey"] = cand20.UF + "|" + cand20.MUNICIPIO.map(norm)
cand20["cd_tse"] = cand20.nkey.map(k2c)
cpf20 = set(zip(cand20.cd_tse, cand20.CPF))
o16["eleito_2016_candidato_em_2020"] = [int((cd, cpf) in cpf20) if pd.notna(cd) else np.nan
                                        for cd, cpf in zip(o16.cd_municipio_tse, o16._cpf)]
# 2020 winners' CPF (match winner ballot name to pindograma 2020 candidate list)
cand20["nk"] = cand20.NOME_URNA.map(norm)
c20map = cand20.drop_duplicates(["cd_tse", "nk"]).set_index(["cd_tse", "nk"])
b20["_nk"] = b20.eleito_nm_urna.map(norm)
b20["_cpf"] = [c20map.CPF.get((cd, k), np.nan) for cd, k in zip(b20.cd_municipio_tse, b20._nk)]
b20["eleito_nm_candidato"] = [c20map.CANDIDATO.get((cd, k), np.nan) for cd, k in zip(b20.cd_municipio_tse, b20._nk)]
cpf16 = set(zip(o16.cd_municipio_tse, o16._cpf))
b20["eleito_2020_igual_eleito_2016_cpf"] = [int((cd, cpf) in cpf16) if isinstance(cpf, str) else np.nan
                                           for cd, cpf in zip(b20.cd_municipio_tse, b20._cpf)]
win20cpf = {(cd, cpf) for cd, cpf in zip(b20.cd_municipio_tse, b20._cpf) if isinstance(cpf, str)}
o16["eleito_2016_reeleito_2020_1t"] = [int((cd, cpf) in win20cpf) if pd.notna(cd) else np.nan
                                       for cd, cpf in zip(o16.cd_municipio_tse, o16._cpf)]

# ---------------------------------------------------------------- 2020 capitals (Wikipedia, both rounds) -> final party
UFN = {"Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM", "Bahia": "BA", "Ceará": "CE", "Espírito Santo": "ES",
       "Goiás": "GO", "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS", "Minas Gerais": "MG", "Pará": "PA",
       "Paraíba": "PB", "Paraná": "PR", "Pernambuco": "PE", "Piauí": "PI", "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN",
       "Rio Grande do Sul": "RS", "Rondônia": "RO", "Roraima": "RR", "Santa Catarina": "SC", "São Paulo": "SP",
       "Sergipe": "SE", "Tocantins": "TO"}
cap = pd.read_csv(os.path.join(OUT, "prefeitos_2020_capitais_wikipedia.csv"))
cap["nkey"] = cap.estado.map(UFN) + "|" + cap.capital.map(norm)
cap["cd_municipio_tse"] = cap.nkey.map(k2c)
assert cap.cd_municipio_tse.notna().all(), cap[cap.cd_municipio_tse.isna()]
PFIX = {"Patriota": "PATRIOTA", "Republicanos": "REPUBLICANOS", "Cidadania": "CIDADANIA", "Avante": "AVANTE"}
capd = dict(zip(cap.cd_municipio_tse.astype(int), cap.partido_na_eleicao.replace(PFIX)))
capn = dict(zip(cap.cd_municipio_tse.astype(int), cap.prefeito_eleito_2020))
b20["eleito_final_sg_partido"] = b20.eleito_sg_partido
b20["fonte_eleito_final"] = np.where(b20.eleito_sg_partido.notna(), "marcofaga_1t", None)
fill = b20.eleito_sg_partido.isna() & b20.cd_municipio_tse.isin(capd.keys())
b20.loc[fill, "eleito_final_sg_partido"] = b20.loc[fill, "cd_municipio_tse"].map(capd)
b20.loc[fill, "eleito_final_nome_wikipedia"] = b20.loc[fill, "cd_municipio_tse"].map(capn)
b20.loc[fill, "fonte_eleito_final"] = "wikipedia_capitais"
# Macapá (election postponed to Dec/2020) is absent from the marcofaga file: add it from the capitals table
mcp = int(cap.loc[cap.capital == "Macapá", "cd_municipio_tse"].iloc[0])
if mcp not in set(b20.cd_municipio_tse):
    b20 = pd.concat([b20, pd.DataFrame([{"ano": 2020, "cd_municipio_tse": mcp, "sg_uf": "AP", "nm_municipio": "MACAPÁ",
                                         "cd_municipio_ibge": tse2ibge.get(mcp), "status_2020": "ausente_no_arquivo_1t",
                                         "eleito_final_sg_partido": capd[mcp], "eleito_final_nome_wikipedia": capn[mcp],
                                         "fonte_eleito_final": "wikipedia_capitais"}])], ignore_index=True)

# ---------------------------------------------------------------- 2024 incumbency proxy (name match with 2020 winner)
w20 = b20.set_index("cd_municipio_tse")
base["prefeito_2020_sg_partido"] = base.cd_municipio_tse.map(w20.eleito_final_sg_partido)
base["prefeito_2020_nm_urna"] = base.cd_municipio_tse.map(w20.eleito_nm_urna.fillna(w20.eleito_final_nome_wikipedia))
base["prefeito_2020_nm_candidato"] = base.cd_municipio_tse.map(w20.eleito_nm_candidato)
base["status_2020"] = base.cd_municipio_tse.map(w20.status_2020)
same_urna = [norm(a) == norm(b) if isinstance(a, str) and isinstance(b, str) and a and b else np.nan
             for a, b in zip(base.eleito_nm_urna, base.prefeito_2020_nm_urna)]
same_nome = [norm(a) == norm(b) if isinstance(a, str) and isinstance(b, str) and a and b else np.nan
             for a, b in zip(base.eleito_nm_candidato, base.prefeito_2020_nm_candidato)]
base["reeleito_proxy_mesmo_nome_urna"] = pd.array(same_urna, dtype="boolean").astype("Int64")
base["reeleito_proxy_mesmo_nome_completo"] = pd.array(same_nome, dtype="boolean").astype("Int64")
base["reeleito_proxy"] = np.where(base.reeleito_proxy_mesmo_nome_completo.notna(),
                                  base.reeleito_proxy_mesmo_nome_completo, base.reeleito_proxy_mesmo_nome_urna)
base["reeleito_proxy"] = pd.to_numeric(base.reeleito_proxy, errors="coerce").astype("Int64")
base.loc[base.eleito_sg_partido.isna() | base.prefeito_2020_sg_partido.isna(), "reeleito_proxy"] = pd.NA

# ---------------------------------------------------------------- write
base.to_csv(os.path.join(OUT, "prefeitos_2024_municipio.csv"), index=False)
b20.drop(columns=["_nk", "_cpf"]).to_csv(os.path.join(OUT, "prefeitos_2020_municipio_1turno.csv"), index=False)
o16.drop(columns=["_cpf"]).to_csv(os.path.join(OUT, "prefeitos_2016_eleitos.csv"), index=False)

# wide panel
pan = xw[(xw.uf != "DF") & (xw.codigo_tse != 30015)][["codigo_tse", "codigo_ibge", "uf", "nome_municipio"]].rename(
    columns={"codigo_tse": "cd_municipio_tse", "codigo_ibge": "cd_municipio_ibge", "uf": "sg_uf"})
o16u = o16.dropna(subset=["cd_municipio_tse"]).copy()
o16u["cd_municipio_tse"] = o16u.cd_municipio_tse.astype(int)
o16u = o16u.groupby("cd_municipio_tse").agg(partido_2016=("eleito_sg_partido_recodificado", lambda s: "|".join(dict.fromkeys(s))),
                                            n_eleitos_2016=("eleito_nm_urna", "size"))
pan = pan.merge(o16u, on="cd_municipio_tse", how="left")
pan = pan.merge(b20[["cd_municipio_tse", "eleito_final_sg_partido", "status_2020", "eleito_candidato_reeleicao",
                     "eleito_2020_igual_eleito_2016_cpf"]].rename(columns={"eleito_final_sg_partido": "partido_2020",
                     "eleito_candidato_reeleicao": "incumbente_2020_flag_tse"}), on="cd_municipio_tse", how="left")
pan = pan.merge(base[["cd_municipio_tse", "eleito_sg_partido", "status_2024", "eleito_share_final", "margem_final",
                      "segundo_turno", "n_candidatos_1t", "reeleito_proxy", "suplementar_eleito_sg_partido"]].rename(
    columns={"eleito_sg_partido": "partido_2024", "eleito_share_final": "share_2024", "margem_final": "margem_2024",
             "segundo_turno": "segundo_turno_2024", "n_candidatos_1t": "n_candidatos_2024",
             "reeleito_proxy": "reeleito_2024_proxy", "suplementar_eleito_sg_partido": "partido_2024_suplementar"}),
    on="cd_municipio_tse", how="left")
pan.to_csv(os.path.join(OUT, "prefeitos_painel_2016_2020_2024.csv"), index=False)

# ---------------------------------------------------------------- checks
print("\n== 2024")
print(base.status_2024.value_counts().to_string())
print("munis", base.cd_municipio_tse.nunique(), "ibge missing", base.cd_municipio_ibge.isna().sum())
print(base.eleito_sg_partido.value_counts().head(8).to_string())
print("2nd round munis", int(base.segundo_turno.sum()))
print("reeleito_proxy", base.reeleito_proxy.value_counts(dropna=False).to_string())
print("\n== 2020")
print(b20.status_2020.value_counts().to_string())
print(b20.fonte_eleito_final.value_counts(dropna=False).to_string())
print(b20.eleito_sg_partido.value_counts().head(8).to_string())
print("winner matched to Herrmann:", b20.eleito_sq_candidato.notna().sum(), "of", b20.eleito_sg_partido.notna().sum())
print("winner incumbent flag:", b20.eleito_candidato_reeleicao.value_counts(dropna=False).to_string())
print("2020 winner == 2016 winner (CPF):", b20.eleito_2020_igual_eleito_2016_cpf.value_counts(dropna=False).to_string())
print("\n== 2016")
print("rows", len(o16), "matched codes", o16.cd_municipio_tse.notna().sum(), "unique munis", o16.cd_municipio_tse.nunique())
print(o16.eleito_sg_partido_recodificado.value_counts().head(8).to_string())
print("\n== panel", pan.shape)
print(pan[["partido_2016", "partido_2020", "partido_2024"]].notna().sum().to_string())
