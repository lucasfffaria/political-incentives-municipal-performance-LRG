"""Aggregate Transparência Brasil Transferegov (transferências especiais 2025) files by
beneficiary municipality and attach the author's party at election (2022 deputies,
2018/2022 senators) by ballot-name match. Usage: python3 -I build_emendas.py <elections_dir>"""
import sys, os, re, json, glob, unicodedata
import pandas as pd
import numpy as np

E = sys.argv[1]
D = os.path.join(E, "emendas_transferegov_tb")
J = os.path.join(E, "camara_2022_kalebefukuda", "json")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"[^A-Z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# elected federal deputies (2022) and senators (2018, 2022)
rows = []
for f in glob.glob(os.path.join(J, "*-c0006.json")) + glob.glob(os.path.join(J, "20*_*-c0005.json")):
    j = json.load(open(f, encoding="utf-8"))
    cargo = "DEPUTADO FEDERAL" if j["carg"][0]["cd"] == "6" else "SENADOR"
    ano = 2022 if cargo == "DEPUTADO FEDERAL" else int(os.path.basename(f)[:4])
    for g in j["carg"][0]["agr"]:
        for p in g["par"]:
            for c in p["cand"]:
                if c["e"] == "s":
                    rows.append({"cargo": cargo, "ano_eleicao": ano, "uf": j["cdabr"].upper(), "nm_urna": c["nmu"],
                                 "partido_eleicao": p["sg"], "nk": norm(c["nmu"])})
parl = pd.DataFrame(rows)
parl.to_csv(os.path.join(D, "parlamentares_eleitos_2018_2022_partido.csv"), index=False)
print("parlamentares:", parl.groupby(["cargo", "ano_eleicao"]).size().to_string())

pl = pd.read_csv(os.path.join(D, "02-plano-acao.csv"), dtype=str)
em = pd.read_csv(os.path.join(D, "03-empenho.csv"), dtype=str)
dh = pd.read_csv(os.path.join(D, "04-documento-habil.csv"), dtype=str)
op = pd.read_csv(os.path.join(D, "05-ordem-pagamento.csv"), dtype=str)

# author -> party (ballot-name match; disambiguate by beneficiary UF when the name repeats)
pl["nk"] = pl.nome_parlamentar_emenda_plano_acao.map(norm)
auth = pl[["codigo_parlamentar_emenda_plano_acao", "nome_parlamentar_emenda_plano_acao", "nk"]].drop_duplicates()
ufmode = pl.groupby("codigo_parlamentar_emenda_plano_acao").uf_beneficiario_plano_acao.agg(lambda s: s.mode().iloc[0])
auth["uf_mais_frequente_beneficiario"] = auth.codigo_parlamentar_emenda_plano_acao.map(ufmode)
m = auth.merge(parl, on="nk", how="left")
m["uf_ok"] = m.uf == m.uf_mais_frequente_beneficiario
m = m.sort_values(["codigo_parlamentar_emenda_plano_acao", "uf_ok"], ascending=[True, False])
cnt = m.groupby("codigo_parlamentar_emenda_plano_acao").nk.transform("size")
m["match"] = np.where(m.cargo.isna(), "sem_match", np.where(cnt == 1, "nome_unico", "nome_repetido_uf"))
m = m.drop_duplicates("codigo_parlamentar_emenda_plano_acao")
# fuzzy fallback within the author's main beneficiary UF: ballot-name tokens contained in the
# parliamentary name (or vice versa), unique candidate required
STOP = {"DR", "DRA", "PR", "PASTOR", "PASTORA", "DE", "DA", "DO", "DOS", "DAS", "E", "JUNIOR", "FILHO", "NETO", "PROFESSOR", "PROFESSORA",
        "DELEGADO", "DELEGADA", "CORONEL", "CAPITAO", "GENERAL", "SARGENTO", "SUBTENENTE", "CABO", "SOLDADO", "COMANDANTE", "MAJOR", "TENENTE"}
tok = lambda s: set(s.split()) - STOP
for i in m.index[m.cargo.isna()]:
    a = tok(m.at[i, "nk"]); uf = m.at[i, "uf_mais_frequente_beneficiario"]
    cand = parl[(parl.uf == uf)]
    SUF = {"FILHO", "JUNIOR", "JR", "NETO", "SOBRINHO"}
    def ok(b):
        tb = tok(b)
        if not tb or not (tb <= a or a <= tb):
            return False
        # a ballot name reduced to one token must not carry a family suffix absent from the author name
        if len(tb) == 1 and (set(b.split()) & SUF) - set(m.at[i, "nk"].split()):
            return False
        return True
    hits = cand[[ok(b) for b in cand.nk]]
    if len(hits) == 1:
        h = hits.iloc[0]
        for c in ["cargo", "ano_eleicao", "uf", "partido_eleicao", "nm_urna"]:
            m.at[i, c] = h[c]
        m.at[i, "match"] = "fuzzy_tokens_uf"
auth = m[["codigo_parlamentar_emenda_plano_acao", "nome_parlamentar_emenda_plano_acao", "uf_mais_frequente_beneficiario",
          "cargo", "ano_eleicao", "uf", "nm_urna", "partido_eleicao", "match"]].rename(columns={"uf": "uf_eleicao", "nm_urna": "nm_urna_eleicao"})
auth.to_csv(os.path.join(D, "autores_emendas_2025_partido.csv"), index=False)
print("autores:", len(auth), auth.match.value_counts().to_string())
print(auth[auth.match == "sem_match"].nome_parlamentar_emenda_plano_acao.head(25).tolist())

# value chain: plano -> empenho -> documento hábil -> ordem de pagamento (OB enviada = pago)
pl["valor_plano"] = pl.valor_custeio_plano_acao.astype(float).fillna(0) + pl.valor_investimento_plano_acao.astype(float).fillna(0)
em["valor_empenho"] = em.valor_empenho.astype(float)
dh["valor_dh"] = dh.valor_dh.astype(float)
ob = op[op.descricao_situacao_op.str.startswith("OB Enviada")].id_dh.unique()
dh["pago"] = dh.id_dh.isin(ob)
pago_emp = dh[dh.pago].groupby("id_empenho").valor_dh.sum()
em["valor_pago"] = em.id_empenho.map(pago_emp).fillna(0)
emp_pl = em.groupby("id_plano_acao").agg(valor_empenhado=("valor_empenho", "sum"), valor_pago=("valor_pago", "sum"))
pl = pl.join(emp_pl, on="id_plano_acao")
pl[["valor_empenhado", "valor_pago"]] = pl[["valor_empenhado", "valor_pago"]].fillna(0)
pl = pl.merge(auth[["codigo_parlamentar_emenda_plano_acao", "cargo", "partido_eleicao"]], on="codigo_parlamentar_emenda_plano_acao", how="left")
keep = ["id_plano_acao", "codigo_plano_acao", "ano_plano_acao", "ano_emenda_parlamentar_plano_acao", "situacao_plano_acao",
        "cnpj_beneficiario_plano_acao", "nome_beneficiario_plano_acao", "uf_beneficiario_plano_acao", "codigo_ibge_municipio",
        "codigo_ibge_uf", "codigo_parlamentar_emenda_plano_acao", "nome_parlamentar_emenda_plano_acao", "cargo", "partido_eleicao",
        "numero_emenda_parlamentar_plano_acao", "codigo_descricao_areas_politicas_publicas_plano_acao",
        "valor_custeio_plano_acao", "valor_investimento_plano_acao", "valor_plano", "valor_empenhado", "valor_pago"]
pl[keep].to_csv(os.path.join(D, "transferencias_especiais_2025_plano_acao_enriquecido.csv"), index=False)

mun = pl[pl.codigo_ibge_municipio.notna()].copy()
agg = mun.groupby("codigo_ibge_municipio").agg(
    uf=("uf_beneficiario_plano_acao", "first"), n_planos=("id_plano_acao", "nunique"),
    n_parlamentares=("codigo_parlamentar_emenda_plano_acao", "nunique"), valor_plano=("valor_plano", "sum"),
    valor_empenhado=("valor_empenhado", "sum"), valor_pago=("valor_pago", "sum"))
agg = agg.reset_index().rename(columns={"codigo_ibge_municipio": "cd_municipio_ibge"})
byp = mun.pivot_table(index="codigo_ibge_municipio", columns="partido_eleicao", values="valor_plano", aggfunc="sum", fill_value=0)
byp.columns = ["valor_plano_partido_" + str(c) for c in byp.columns]
agg = agg.merge(byp, left_on="cd_municipio_ibge", right_index=True, how="left")
agg.to_csv(os.path.join(D, "transferencias_especiais_2025_por_municipio.csv"), index=False)
print("munis", len(agg), "valor_plano bn", round(agg.valor_plano.sum() / 1e9, 3), "empenhado bn", round(agg.valor_empenhado.sum() / 1e9, 3),
      "pago bn", round(agg.valor_pago.sum() / 1e9, 3))
print("non-municipal beneficiaries (no IBGE muni code):", pl.codigo_ibge_municipio.isna().sum(), "plans; value bn",
      round(pl[pl.codigo_ibge_municipio.isna()].valor_plano.sum() / 1e9, 3))
print(pl.groupby("partido_eleicao", dropna=False).valor_plano.sum().sort_values(ascending=False).head(12).div(1e6).round(1).to_string())
