"""
01_build_national.py -- national municipal dataset for the LRG evaluation (5,570 municipalities).

Builds, from the raw public files in data/raw (all copies of official data, see data/raw/*/SOURCES.md):
  data/derived/municipios_base.csv   one row per municipality: population, region, economy, fiscal, social,
                                     political (2016/2020/2024 mayors), amendments (2025 transferencias
                                     especiais), Bolsa Familia, Census 2022 variables, FPM (computed)
  data/derived/panel_*.csv           long panels used to estimate the measurement properties of indicators
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json
import numpy as np
import pandas as pd
import pyreadr

RAW = _ROOT + '/data/raw'
DER = _ROOT + '/data/derived'
_os.makedirs(DER, exist_ok=True)
REG = {1: 'N', 2: 'NE', 3: 'SE', 4: 'S', 5: 'CO'}

# ------------------------------------------------------------------ master list and population
pop = list(pyreadr.read_r(RAW + '/education/ibge_pop.rds').values())[0]
pop['cod_ibge'] = pop.code_muni.astype(int); pop['year'] = pop.year.astype(int)
popw = pop.pivot_table(index='cod_ibge', columns='year', values='pop')
cen = pd.read_csv(RAW + '/fiscal/ibge_cempre_censo/ibge_cempre2024_censo2022_municipios.csv')
cen = cen.rename(columns={'populacao_censo_2022_2022': 'pop2022_censo'})
mun = pd.read_csv(RAW + '/education/municipios.csv').rename(columns={'codigo_ibge': 'cod_ibge'})
base = cen[['cod_ibge', 'nome', 'uf', 'pop2022_censo']].copy()
base = base[base.pop2022_censo.notna()].copy()
base['cod_ibge'] = base.cod_ibge.astype(int)
base['uf_code'] = base.cod_ibge // 100000
base['region'] = (base.uf_code // 10).map(REG)
for y in [2010, 2016, 2020, 2021, 2022, 2024, 2025]:
    base[f'pop{y}'] = base.cod_ibge.map(popw[y])
base['pop2022'] = base.pop2022_censo
base = base.merge(mun[['cod_ibge', 'latitude', 'longitude', 'capital']], on='cod_ibge', how='left')
base['capital'] = base.capital.fillna(0).astype(int)
# Census 2022 attributes
keep = ['domicilios_total_2022', 'agua_rede_geral_2022', 'esgoto_rede_2022', 'lixo_coletado_2022',
        'alfabetizados_15_mais_2022', 'pessoas_15_mais_2022', 'pessoas_18_mais_2022', 'moradores_10_mais_2022',
        'forca_de_trabalho_14_mais_2022', 'ocupados_14_mais_2022', 'ocupados_contribuintes_2022',
        'rendimento_medio_trabalho_2022', 'superior_completo_2022', 'massa_rendimento_trabalho_2022',
        'assalariados_empresas_2024', 'empresas_atuantes_2024', 'pib_municipal_2023']
base = base.merge(cen[['cod_ibge'] + keep], on='cod_ibge', how='left')
base['pop0_9_2022'] = base.pop2022 - base.moradores_10_mais_2022
base['sh_water_census'] = base.agua_rede_geral_2022 / base.domicilios_total_2022
base['sh_sewer_census'] = base.esgoto_rede_2022 / base.domicilios_total_2022
base['literacy15_census'] = base.alfabetizados_15_mais_2022 / base.pessoas_15_mais_2022
base['formal_census'] = base.ocupados_contribuintes_2022 / base.ocupados_14_mais_2022
base['higher_ed_share'] = base.superior_completo_2022 / base.pessoas_18_mais_2022

# ------------------------------------------------------------------ economy: GDP and value added
pib = pd.read_csv(RAW + '/fiscal/pib_municipios/pib_municipios_2010_2023_slim.csv')
pib = pib.rename(columns={'cod_ibge': 'cod_ibge'})
p21 = pib[pib.ano == 2021].set_index('cod_ibge')
p23 = pib[pib.ano == 2023].set_index('cod_ibge')
base['gdp_2021'] = base.cod_ibge.map(p21.pib) * 1e3
base['gdp_2023'] = base.cod_ibge.map(p23.pib) * 1e3
base['gdp_pc_2021'] = base.gdp_2021 / base.pop2021
base['va_pub_share_2021'] = base.cod_ibge.map(p21.vab_adm_publica_defesa_educ_saude_seg_social / p21.vab_total)
base['va_agro_share_2021'] = base.cod_ibge.map(p21.vab_agropecuaria / p21.vab_total)
base['semiarido'] = base.cod_ibge.map(p21.semiarido)
base['amazonia_legal'] = base.cod_ibge.map(p21.amazonia_legal)
base['hierarquia_urbana'] = base.cod_ibge.map(p21.hierarquia_urbana)
pan_va = pib[pib.ano <= 2021][['cod_ibge', 'ano', 'vab_adm_publica_defesa_educ_saude_seg_social', 'vab_total',
                               'vab_agropecuaria']].copy()
pan_va['value'] = 100 * (1 - pan_va.vab_adm_publica_defesa_educ_saude_seg_social / pan_va.vab_total)
pan_va = pan_va.rename(columns={'ano': 'year'})[['cod_ibge', 'year', 'value']]
pan_va.to_csv(DER + '/panel_K2_private_va_share.csv', index=False)

# ------------------------------------------------------------------ formal employment (RAIS, 31 Dec)
rais = pd.read_csv(RAW + '/fiscal/rais_municipal/rais_vinculos_municipio_setor_2006_2024.csv')
rais = rais.rename(columns={'id_municipio': 'cod_ibge', 'ano': 'year'})
rais['pop'] = [popw.at[c, y] if (c in popw.index and y in popw.columns) else np.nan
               for c, y in zip(rais.cod_ibge, rais.year)]
rais['value'] = 100 * rais.ativos_empresas / rais['pop']          # private formal jobs per 100 inhabitants
rais[['cod_ibge', 'year', 'value', 'pop']].to_csv(DER + '/panel_K1_formal_jobs.csv', index=False)
r24 = rais[rais.year == 2024].set_index('cod_ibge')
base['jobs_private_2024'] = base.cod_ibge.map(r24.ativos_empresas)
base['jobs_public_2024'] = base.cod_ibge.map(r24.ativos_adm_publica)
base['K1_formal_jobs_2024'] = 100 * base.jobs_private_2024 / base.pop2024
r22 = rais[rais.year == 2022].set_index('cod_ibge')
base['jobs_public_2022'] = base.cod_ibge.map(r22.ativos_adm_publica)

# ------------------------------------------------------------------ Bolsa Familia and transfers dependence
fol = pd.read_csv(RAW + '/fiscal/emprego_bolsafamilia/folha_mun_202512_flat.csv')
fol = fol.set_index('cod_ibge')
base['bf_families_2025'] = base.cod_ibge.map(fol.bolsa_familia_n)
base['bf_people_2025'] = base.cod_ibge.map(fol.bolsa_familia_pessoas)
base['pension_n_2025'] = base.cod_ibge.map(fol.previdencia_n)
base['public_wage_n_2025'] = base.cod_ibge.map(fol.salario_publico_n)
base['public_wage_mun_n_2025'] = base.cod_ibge.map(fol.salario_publico_n_municipal)
base['private_wage_n_2025'] = base.cod_ibge.map(fol.salario_privado_n)
base['bf_share_households'] = base.bf_families_2025 / base.domicilios_total_2022
bf24 = pd.read_csv(RAW + '/fiscal/emprego_bolsafamilia/bolsa_familia_mun_202405.csv').set_index('codigo_municipio_ibge')
base['bf_payments_2024_05'] = base.cod_ibge.map(bf24.n_pagamentos_familias)

# ------------------------------------------------------------------ fiscal (SICONFI, partial coverage)
rreo = pd.read_csv(RAW + '/fiscal/siconfi_rreo_rgf/siconfi_rreo_anexo01_receitas_correntes_2024.csv').set_index('cod_ibge')
base['rev_current_2024'] = base.cod_ibge.map(rreo.receitas_correntes_total_declarado)
base['rev_taxes_2024'] = base.cod_ibge.map(rreo.det_impostos)
base['rev_fees_2024'] = base.cod_ibge.map(rreo.det_taxas)
base['rev_union_2024'] = base.cod_ibge.map(rreo.det_transferencias_da_uniao_e_de_suas_entidades)
base['rev_state_2024'] = base.cod_ibge.map(rreo.det_transferencias_dos_estados_e_do_distrito_federal_e_de_suas_entidades)
base['own_tax_share_2024'] = base.rev_taxes_2024 / base.rev_current_2024
rgf = pd.read_csv(RAW + '/fiscal/siconfi_rreo_rgf/siconfi_rgf_anexo01_pct_pessoal_serie_2020_2024.csv')
rgf = rgf[(rgf.quadrimestre == 3) & rgf.pct_pessoal_rcl_ajustada.notna()]
rgf = rgf.rename(columns={'exercicio': 'year', 'pct_pessoal_rcl_ajustada': 'value'})
rgf[['cod_ibge', 'year', 'value']].to_csv(DER + '/panel_F_personnel_rcl.csv', index=False)
base['personnel_rcl_2024'] = base.cod_ibge.map(rgf[rgf.year == 2024].set_index('cod_ibge').value)

# ------------------------------------------------------------------ FPM 2024 (computed from the legal rules)
# Interior: 86.4% of FPM, split by the fixed state shares (Res. TCU 242/1990), then by population coefficients
# (DL 1.881/1981); reserve: 3.6% to interior municipalities with coefficient 4.0; capitals: 10% by population x
# inverse per-capita income. FPM gross 2024 ~ R$ 216 bn (Tesouro; net of FUNDEB R$ 177 bn).
STATE_SHARE = {'AC': 0.2630, 'AL': 2.0883, 'AP': 0.1392, 'AM': 1.2452, 'BA': 9.2695, 'CE': 4.5864, 'ES': 1.7595,
               'GO': 3.7318, 'MA': 3.9715, 'MT': 1.8949, 'MS': 1.5004, 'MG': 14.1846, 'PA': 3.2948, 'PB': 3.1942,
               'PR': 7.2857, 'PE': 4.7952, 'PI': 2.4015, 'RJ': 2.7379, 'RN': 2.4324, 'RS': 7.3011, 'RO': 0.7464,
               'RR': 0.0851, 'SC': 4.1997, 'SP': 14.2620, 'SE': 1.3342, 'TO': 1.2955}
brk = [10188, 13584, 16980, 23772, 30564, 37356, 44148, 50940, 61128, 71316, 81504, 91692, 101880, 115464,
       129048, 142632, 156216]
coefs = np.arange(0.6, 4.01, 0.2)
FPM_GROSS = 216e9
b = base[base.uf != 'DF'].copy()
b['coef'] = coefs[np.searchsorted(brk, b.pop2024.fillna(b.pop2022).values, side='left')]
inte = b[b.capital == 0].copy()
inte['fpm_int'] = 0.864 * FPM_GROSS * inte.uf.map(STATE_SHARE) / 100 * inte.coef / inte.groupby('uf').coef.transform('sum')
gpc = b.gdp_pc_2021 / np.nanmedian(b.gdp_pc_2021)
res = inte[inte.coef >= 3.99].copy()
w = res.pop2024 / gpc.loc[res.index]
inte.loc[res.index, 'fpm_int'] += 0.036 * FPM_GROSS * w / w.sum()
cap = b[b.capital == 1].copy()
wc = cap.pop2024 / gpc.loc[cap.index]
cap['fpm_int'] = 0.10 * FPM_GROSS * wc / wc.sum()
fpm = pd.concat([inte, cap]).set_index('cod_ibge').fpm_int
base['fpm_gross_2024'] = base.cod_ibge.map(fpm)
base['fpm_coef'] = base.cod_ibge.map(b.set_index('cod_ibge').coef)

# ------------------------------------------------------------------ parliamentary amendments 2025 (transferencias especiais)
em = pd.read_csv(RAW + '/elections/emendas_transferegov_tb/transferencias_especiais_2025_por_municipio.csv')
em = em.set_index('cd_municipio_ibge')
base['pix_plan_2025'] = base.cod_ibge.map(em.valor_plano).fillna(0)
base['pix_paid_2025'] = base.cod_ibge.map(em.valor_pago).fillna(0)
base['pix_n_authors_2025'] = base.cod_ibge.map(em.n_parlamentares).fillna(0)
pcols = [c for c in em.columns if c.startswith('valor_plano_partido_')]
emp = em[pcols].copy(); emp.columns = [c.replace('valor_plano_partido_', '') for c in pcols]
emp.to_csv(DER + '/pix_2025_by_author_party.csv')

# ------------------------------------------------------------------ mayors 2016, 2020, 2024
pm = pd.read_csv(RAW + '/elections/derived/prefeitos_2024_municipio.csv')
pm = pm.set_index('cd_municipio_ibge')
party24 = pm.eleito_sg_partido.where(pm.eleito_sg_partido.notna(), pm.suplementar_eleito_sg_partido)
base['party_2024'] = base.cod_ibge.map(party24)
base['share_2024'] = base.cod_ibge.map(pm.eleito_share_final)
base['margin_2024'] = base.cod_ibge.map(pm.margem_final)
base['runoff_2024'] = base.cod_ibge.map(pm.segundo_turno)
base['n_cand_2024'] = base.cod_ibge.map(pm.n_candidatos_1t)
base['reelected_2024'] = base.cod_ibge.map(pm.reeleito_proxy)
pp = pd.read_csv(RAW + '/elections/derived/prefeitos_painel_2016_2020_2024.csv').set_index('cd_municipio_ibge')
base['party_2016'] = base.cod_ibge.map(pp.partido_2016)
base['party_2020'] = base.cod_ibge.map(pp.partido_2020)
base['reelected_2020'] = base.cod_ibge.map(pp.eleito_2020_igual_eleito_2016_cpf)

# ------------------------------------------------------------------ social: favelas, illiteracy, homicides 2022, robberies
fav = pd.read_csv(RAW + '/social/favelas/favelas_pop_por_municipio_2022_derivado.csv').set_index('cod_ibge')
base['pop_favela_2022'] = base.cod_ibge.map(fav.pop_fcu_total_pessoas).fillna(0)
base['K5_favela_share'] = 100 * base.pop_favela_2022 / base.pop2022
pan = pd.read_csv(RAW + '/social/painel_socioambiental/painel_socioambiental_municipios_wide.csv').set_index('cod_ibge')
base['hom_rate_2022'] = base.cod_ibge.map(pan.tx_homicidios)
base['robbery_rate_2023'] = base.cod_ibge.map(pan.tx_roubos)
base['illiteracy_15_painel'] = base.cod_ibge.map(pan.taxa_analf)
base['water_cov_sinisa'] = base.cod_ibge.map(pan.agua_cob)
base['sewer_cov_sinisa'] = base.cod_ibge.map(pan.esgoto_cob)
base['sewer_treat_sinisa'] = base.cod_ibge.map(pan.esgoto_trat)
base['sewer_provider'] = base.cod_ibge.map(pan.emp_esgoto)
base['water_provider'] = base.cod_ibge.map(pan.emp_agua)

# homicides panel (Atlas da Violencia rates 1996-2016 + 2022), converted to expected counts with population
hom = pd.read_csv(RAW + '/social/atlas_violencia/atlas_taxa_homicidios_municipios_1996_2016.csv', sep=';')
hom = hom.rename(columns={'cod': 'cod_ibge', 'período': 'year', 'valor': 'value'})
h22 = base[['cod_ibge', 'hom_rate_2022']].rename(columns={'hom_rate_2022': 'value'}).assign(year=2022)
hom = pd.concat([hom[['cod_ibge', 'year', 'value']], h22[['cod_ibge', 'year', 'value']]])
hom['pop'] = [popw.at[c, y] if (c in popw.index and y in popw.columns) else np.nan
              for c, y in zip(hom.cod_ibge, hom.year)]
hom['count'] = hom.value * hom['pop'] / 1e5
hom.to_csv(DER + '/panel_K7_homicides.csv', index=False)

# sanitation panel (SNIS 1995-2022): sewage collection (IN056, % of population) and water (IN055)
sn = pd.read_csv(RAW + '/social/snis/br_mdr_snis_municipio_agua_esgoto.csv',
                 usecols=['ano', 'id_municipio', 'populacao_atendida_agua', 'populacao_atentida_esgoto',
                          'indice_atendimento_total_agua', 'indice_atendimento_esgoto_agua',
                          'indice_tratamento_esgoto', 'indice_esgotamento_agua_consumida'])
sn = sn.rename(columns={'id_municipio': 'cod_ibge', 'ano': 'year'})
sn['pop'] = [popw.at[c, y] if (c in popw.index and y in popw.columns) else np.nan
             for c, y in zip(sn.cod_ibge, sn.year)]
sn['sewer_pop_share'] = 100 * sn.populacao_atentida_esgoto / sn['pop']
sn['water_pop_share'] = 100 * sn.populacao_atendida_agua / sn['pop']
sn.to_csv(DER + '/panel_K6_sanitation_snis.csv', index=False)
s22 = sn[sn.year == 2022].set_index('cod_ibge')
base['sewer_snis_2022'] = base.cod_ibge.map(s22.sewer_pop_share)
base['water_snis_2022'] = base.cod_ibge.map(s22.water_pop_share)

# literacy (Indicador Crianca Alfabetizada), municipal network
ica = pd.read_csv(RAW + '/social/alfabetizacao/ica_resultados_municipio_2023_2024.csv')
ica = ica[(ica.rede_padronizada == 'municipal')].rename(columns={'id_municipio': 'cod_ibge', 'ano': 'year',
                                                                 'taxa_alfabetizacao': 'value'})
ica[['cod_ibge', 'year', 'value', 'media_portugues']].to_csv(DER + '/panel_K3_literacy.csv', index=False)
for y in [2023, 2024]:
    base[f'K3_literacy_{y}'] = base.cod_ibge.map(ica[ica.year == y].set_index('cod_ibge').value)

# daycare/preschool coverage (School Census enrolments, all networks) over estimated population 0-5
cs = pd.read_csv(RAW + '/education/dp_stg_censo_sinopse.csv')
cs = cs.rename(columns={'ano': 'year'})
cs['enrol05'] = cs.mat_creche + cs.mat_pre_escola
p05_2022 = 0.6 * base.set_index('cod_ibge').pop0_9_2022
cs['pop05'] = [p05_2022.get(c, np.nan) * (popw.at[c, y] / popw.at[c, 2022]) * 1.009 ** (2022 - y)
               if (c in popw.index and y in popw.columns) else np.nan for c, y in zip(cs.cod_ibge, cs.year)]
cs['value'] = 100 * cs.enrol05 / cs.pop05
cs[['cod_ibge', 'year', 'value', 'enrol05', 'pop05']].to_csv(DER + '/panel_K4_daycare.csv', index=False)
base['K4_daycare_2023'] = base.cod_ibge.map(cs[cs.year == cs.year.max()].set_index('cod_ibge').value)
base['K4_year'] = cs.year.max()

# IDEB (anos iniciais, municipal network) 2015-2025
ideb = pd.read_csv(RAW + '/education/panel_ideb_municipal.csv')
ideb[['cod_ibge', 'ano', 'ideb', 'N', 'P']].rename(columns={'ano': 'year', 'ideb': 'value'}).to_csv(
    DER + '/panel_E_ideb.csv', index=False)
base['ideb_2025'] = base.cod_ibge.map(ideb[ideb.ano == 2025].set_index('cod_ibge').ideb)
base['ideb_2023'] = base.cod_ibge.map(ideb[ideb.ano == 2023].set_index('cod_ibge').ideb)
inse = ideb.groupby('cod_ibge').inse_score_2021.first()
base['inse_2021'] = base.cod_ibge.map(inse)

# current values of the scorecard indicators (latest available)
base['K2_private_va_2021'] = 100 * (1 - base.va_pub_share_2021)
base['K6_sewer_2022'] = base.sewer_snis_2022
base['K7_hom_rate_2022'] = base.hom_rate_2022

base = base.sort_values('cod_ibge').reset_index(drop=True)
base.to_csv(DER + '/municipios_base.csv', index=False)

# ------------------------------------------------------------------ checks
print('municipalities:', len(base), '| population 2022 (M): %.1f' % (base.pop2022.sum() / 1e6))
print('regions:', base.region.value_counts().to_dict())
print('FPM computed (R$ bn): %.1f; per capita median R$ %.0f' % (base.fpm_gross_2024.sum() / 1e9,
      np.nanmedian(base.fpm_gross_2024 / base.pop2024)))
print('Pix 2025 plan (R$ bn): %.2f, municipalities with Pix: %d' % (base.pix_plan_2025.sum() / 1e9, (base.pix_plan_2025 > 0).sum()))
print('mayors 2024 with party:', base.party_2024.notna().sum())
print('coverage of key vars:')
for c in ['K1_formal_jobs_2024', 'K2_private_va_2021', 'K3_literacy_2024', 'K4_daycare_2023', 'K5_favela_share',
          'K6_sewer_2022', 'K7_hom_rate_2022', 'ideb_2025', 'own_tax_share_2024', 'personnel_rcl_2024',
          'bf_share_households', 'gdp_pc_2021', 'sh_sewer_census', 'formal_census']:
    print('  %-22s n=%4d  mean=%8.2f  median=%8.2f' % (c, base[c].notna().sum(), base[c].mean(), base[c].median()))
