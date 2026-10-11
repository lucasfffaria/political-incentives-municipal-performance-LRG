"""
15_verdict.py -- the assessment of the evidence on each causal link of the LRG's theory of change (Figure 1),
applied with explicit rules to the numbers in output/numbers.json (simulation and real data) and, for the links
the simulation cannot test, to the evidence cited in the article. Writes output/verdict.json, read by
11_figures_diagrams.py and by the article (Table 10 and Figure 13; rules in Section S8.10 of the Supplementary
Material). The assessments describe how far the evidence supports each link; they do not weigh the effects of
the law against its costs.

Assessments: 'strong' (supported, sizeable), 'partial' (supported, small), 'weak' (weak or unproven),
'contrary' (contradicted).
"""
import os as _os
_ROOT = _os.environ.get('LRG_ROOT') or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json

OUT = _ROOT + '/output'
N = json.load(open(OUT + '/numbers.json'))
D = N['designs']; SH = N['shapley']; AP = D['F11111']
med = lambda o: o['med']
tot = med(SH['eff_comp']['total'])
share = lambda p, out='eff_comp': med(SH[out][p]) / med(SH[out]['total']) if med(SH[out]['total']) else 0.0
term_max = 0.033                     # largest mayoral-term share of variance in Table 5 (homicides)
V, why = {}, {}


def setv(link, v, reason):
    V[link] = v; why[link] = reason


IE = N.get('incentive_estimates', {})
er = {(r['year'], r['var']): r for r in IE.get('electoral_returns', [])}
c20 = er.get((2020, 'composite (SD of composite)'), {}); c24 = er.get((2024, 'composite (SD of composite)'), {})
rdv = {r['var']: r for r in IE.get('rd', [])}
# scorecard
setv('P_score->C_voters', 'weak', f"voters reward measured performance by {c24.get('coef_pp', 0):.1f}-{c20.get('coef_pp', 0):.1f} points of re-election per SD (2024, 2020); "
     'routine performance information has no average electoral effect (Dunning et al., 2019)')
setv('P_score->C_effort', 'weak' if abs(med(SH['eff_comp']['I'])) < 0.1 * tot else 'partial',
     f"publishing the scorecard alone: {med(SH['eff_comp']['I']):+.3f} SD")
# sanctions
s_real, s_cos = share('S'), share('S', 'cosmetic')
setv('P_sanc->C_effort', 'contrary' if med(SH['eff_comp']['S']) < 0 else
     ('weak' if (s_real < 0.25 or med(SH['cosmetic']['S']) > med(SH['eff_comp']['S'])) else 'partial'),
     f'sanctions: {100 * s_real:.0f}% of the real effect, {100 * s_cos:.0f}% of the cosmetic gap')
attrib = 1 - med(AP['wrongful']) - med(AP['place_driven'])
setv('P_sanc->C_select', 'contrary' if (attrib < 0.10 or med(SH['thetapw']['S']) < 0) else 'weak',
     f'{100 * attrib:.1f}% of bans attributable to the mayor; competence effect of sanctions {med(SH["thetapw"]["S"]):+.3f} SD')
# money
f_share = share('F'); f_pw = share('F', 'effpw_comp')
setv('P_fpm->C_effort', 'contrary' if med(SH['eff_comp']['F']) < 0 else ('weak' if (f_pw < 0.15 or med(AP['pts_corr']) < 0.8) else 'partial'),
     f"FPM tranche: {100 * f_share:.0f}% of the average effect, {100 * f_pw:.0f}% of the population-weighted one; points-truth correlation {med(AP['pts_corr']):.2f}")
a_share = share('A')
setv('P_amend->C_effort', 'strong' if (a_share >= 0.35 and SH['eff_comp']['A']['p5'] > 0) else ('partial' if SH['eff_comp']['A']['p5'] > 0 else 'weak'),
     f'tied amendments: {100 * a_share:.0f}% of the effect')
setv('P_amend->C_fuel', 'strong' if (med(AP['disc_2036']) <= 0.7 and med(SH['incumb_win']['A']) < -2) else 'partial',
     f"discretionary money x{med(AP['disc_2036']):.2f}; incumbents' re-election {med(SH['incumb_win']['A']):+.1f} pp")
# capacity
c_share = share('C')
setv('P_cap->C_effort', 'strong' if c_share >= 0.35 else ('partial' if SH['eff_comp']['C']['p5'] > 0 else 'weak'),
     f'commissioners: {100 * c_share:.0f}% of the effect')
# party funds
so_theta = N.get('sobol', {}).get('theta', {}).get('Party pressure and recruitment', 1.0)
setv('P_party->C_select', 'weak',
     f"population-weighted competence {med(SH['thetapw']['P']):+.3f} SD, resting on the recruitment assumption (Sobol {so_theta:.2f}); "
     f"six largest parties' share of the FP {med(SH['fp_big6']['P']):+.1f} pp")
# channels to results
setv('C_effort->R_serv', 'strong' if tot >= 0.25 else ('partial' if SH['eff_comp']['total']['p5'] > 0 else 'weak'),
     f'average effect {tot:+.3f} SD')
setv('C_select->R_serv', 'weak' if term_max < 0.05 else 'partial', 'the mayor-term component is at most 3.3% of the variance (Table 5)')
# v4: the close races estimate a joint effect of continuity and eligibility; the electoral incentive is bounded, not identified
dec = {r['var']: r for r in IE.get('decomposition', []) if r['version'] == 'adjusted'}
setv('C_voters->R_serv', 'weak', f"the joint effect of continuity and lost eligibility in the close 2020 races is small "
     f"(daycare {rdv.get('day_21', {}).get('coef', 0):+.2f}, jobs {rdv.get('jobs_21', {}).get('coef', 0):+.2f} SD, lame minus first-term); "
     f"the electoral incentive on learning is bounded between {dec.get('ideb_21', {}).get('E_lo_ci', 0):.2f} and {dec.get('ideb_21', {}).get('E_hi_ci', 0):.2f} SD, not identified")
k12 = max(abs(med(AP['eff_K']['K1'])), abs(med(AP['eff_K']['K2'])))
setv('C_effort->R_econ', 'weak' if k12 < 0.02 else 'partial', f'largest effect on the economic indicators {k12:.3f} SD')
setv('R_serv->R_econ', 'weak', 'no measurable effect within the horizon')
setv('R_econ->R_dep', 'weak' if abs(med(AP['vul_2036'])) < 0.01 else 'partial', f"vulnerability {100 * med(AP['vul_2036']):+.2f} pp")
ca = N.get('chain', {}).get('F00100', {}).get('delta_centrao_pp', [0, 0, 0])
setv('C_fuel->R_brasilia', 'partial' if (ca[2] < 0) else 'weak', f'tied amendments alone: centrao vote {ca[1]:+.1f} pp [{ca[0]:.1f}, {ca[2]:.1f}]')
setv('R_dep->R_brasilia', 'weak', 'dependence barely changes')
json.dump(dict(links=V, reasons=why), open(OUT + '/verdict.json', 'w'), indent=1)
for k in V:
    print(f'{k:22s} {V[k]:9s} {why[k]}')
