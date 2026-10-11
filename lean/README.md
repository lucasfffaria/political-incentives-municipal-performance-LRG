# Formal proofs of the analytical model (Lean 4)

This folder states in Lean 4, with the Mathlib library, the mathematical results of Section S2 of the Supplementary
Material (the derivations, numbered (S2.1) to (S2.23), and the ten propositions P1 to P10) and the equations of
Section 3 of the article on which they rest, and proves them. Compiling the folder checks every proof by machine.
What is checked is the mathematics of the model: the empirical results of the article, the evidence cited in the
notes "Where the article tests it", and the simulation are not, and cannot be, proved here.

**Status.** The project builds without errors with Lean `v4.15.0` and Mathlib `v4.15.0` (built on 9 October 2026,
on Windows). Every theorem is proved, and the main theorems, those listed in `LRGProofs/Axioms.lean`, rest only on
Lean's three standard axioms (`propext`, `Classical.choice` and `Quot.sound`); no proof is left unfinished, since
`sorryAx` does not appear. The record of that build is in `results/`:

* `results/build_log.txt`, the output of `lake exe cache get` and `lake build`. Its warnings are style notes of
  Mathlib's linters (a `;` would suffice where `<;>` is used, and two `ring` calls were not needed); they do not
  affect any proof.
* `results/SHA256SUMS.txt`, the hashes of the files that were built. From this folder,
  `sha256sum -c results/SHA256SUMS.txt` (Linux, macOS or Git Bash) checks that the files are those of the build.

`lake-manifest.json` records the exact revision of Mathlib and of each package it uses, so that a new build uses
the same code.

## How to build

1. Install Lean through `elan`. On Windows, in PowerShell:
   ```
   curl -O --location https://raw.githubusercontent.com/leanprover/elan/master/elan-init.ps1
   powershell -ExecutionPolicy Bypass -f elan-init.ps1
   del elan-init.ps1
   ```
   (or install Visual Studio Code with the "Lean 4" extension, which installs `elan`). On Linux or macOS:
   `curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh`.
2. In this folder, download the compiled Mathlib and build:
   ```
   lake exe cache get
   lake build
   ```
   The first command fetches Mathlib at the revision of `lake-manifest.json` (about 5 GB, in the folder `.lake`);
   `elan` installs the matching Lean automatically. The build of 9 October 2026 ran in place, in a path with
   accents and without spaces; paths with spaces are best avoided.
3. The build succeeds only if every proof is complete and correct. It also prints, for the main theorems, the
   axioms on which their proofs rest (file `LRGProofs/Axioms.lean`): only `propext`, `Classical.choice` and
   `Quot.sound`, Lean's standard axioms, should appear; `sorryAx` would reveal an unfinished proof.
4. The folder `.lake` is only a download and build cache. It is excluded from the repository by `.gitignore`, can
   be deleted after the build and is recreated by `lake exe cache get`.

If `lake exe cache get` cannot find the compiled Mathlib for this version, `lake build` would compile Mathlib
itself (several hours). The alternative is to move both pins to a newer Lean and Mathlib release; the proofs use
few named lemmas, but a newer Mathlib may have renamed some of them.

## What each file proves

Theorem names are those of the files, in the namespace `LRG`. Variables follow the text: `δ` is the effort scale,
`I` the marginal expected incentive, `c` capacity, `m = 1 + φθ` the competence multiplier, `κ` the cost of
manipulation, `σ` the noise, `L` the loss from a ban, `η` the dependence of implementation on incentives.

| Text | Statement | Lean |
|---|---|---|
| Eq. (5), (6) | The marginal cost (6) is the derivative of the cost (5), rises with effort, equals `4a/(4δ - a)` | `hasDerivAt_cost`, `marginalCost_lt`, `marginalCost_eq` (`Effort.lean`) |
| Eq. (7), (S2.1) | The effort rule solves the first-order condition, is its only solution below the ceiling, and maximises `I a - C(a)` | `effort_foc`, `marginalCost_effort`, `effort_unique`, `effort_maximizes` |
| (S2.2) | `a²/(2δ) ≤ C(a) ≤ (a²/(2δ))/(1 - a/(4δ))`, so `C(a) ≈ a²/(2δ)` for small efforts | `cost_ge_quadratic`, `cost_le` |
| (S2.3) | `δI(1 - I/4) ≤ a* ≤ δI` and `|a* - δI| ≤ δI²/4` | `lower_le_effort`, `effort_le_linear`, `effort_approx` |
| After (S2.3) | Effort stays below and approaches the ceiling `4δ`; it rises with `I` with diminishing returns; the textbook contract gives a gain `α²b/k` | `effort_lt_ceiling`, `effort_approaches_ceiling`, `effort_strictMono`, `effort_diminishing`, `linear_contract` (`Quadratic.lean`) |
| Eq. (9) | Manipulation `g* = I/κ` is the unique best response to a quadratic cost | `manipulation_optimal`, `quadratic_argmax_unique` (`Quadratic.lean`) |
| (S2.4) to (S2.6) | The cosmetic share of the gain from a bonus is `1/(1 + c m δ κ)`, and `1/(1 + c δ κ)` for an average mayor | `cosmetic_share_bonus`, `cosmetic_share_average_mayor` (`Cosmetic.lean`) |
| (S2.7) | The weight falls with the noise; for a risk-neutral agent it falls with the substitution; with a risk-averse agent it can rise with it (explicit example) | `hmWeight_falls_with_noise`, `hmWeight_risk_neutral`, `hm_numerator_falls_with_substitution`, `hmWeight_can_rise_with_substitution` (`ContractTheory.lean`) |
| (S2.8) | The rate is below one exactly when `ρσV < σP`; with equal dispersion, unless the responses are perfectly correlated; it can exceed one otherwise (explicit example) | `bakerRate_lt_one_iff`, `bakerRate_equal_dispersion`, `bakerRate_aligned`, `bakerRate_can_exceed_one` |
| (S2.9), (S2.10) | The probability of a sanction | `sanctionProb` (`Sanctions.lean`) |
| (S2.11) | Mobilisation `x* = kγv(1 - t)D/κ` is the best response to a quadratic cost | `mobilisation`, `mobilisation_optimal` (`Clientelism.lean`) |
| P1, (S2.12) to (S2.14) | Place and mayor move the probability of a sanction by the same factor `f(z)/σ` per unit; `corr(ŷ, θ) = λσθ/σŷ`; no function of `ŷ` is more correlated with `θ` | `hasDerivAt_sanctionProb_place`, `hasDerivAt_sanctionProb_mayor`, `sanction_response_ratio`, `corr_reported_competence`, `corr_function_le` (`Information.lean`) |
| P2, (S2.15) to (S2.17) | The sanction term peaks at `L/(√(2π)σ)`, which falls with the noise; mistaken sanctions rise with the noise; failing at least one of `K` tests tends to certainty | `sanction_term_peak`, `sanction_term_le_peak`, `sanction_term_peak_falls_with_noise`, `misclassification_mono`, `misclassification_strictMono`, `fail_at_least_one_mono`, `fail_at_least_one_tendsto` |
| P3, (S2.18) | The cosmetic share is `1/(1 + κ c m a/I)`, falls with capacity and reduces to (S2.6) | `cosmetic_share_identity`, `cosmetic_share_falls_with_capacity`, `cosmetic_share_linear_region` |
| P4, (S2.19) | `cov(Δŷ, ε_{t-1}) = -var(ε_{t-1})`; with a concave value of money, moving money towards the higher level lowers the total | `cov_change_lagged_noise`, `concave_transfer` (`Money.lean`) |
| P5, (S2.20) | The party score rises by recruiting a mayor with positive points or by improving one's own mayors | `partyScore`, `partyScore_recruit`, `partyScore_recruit_gain`, `partyScore_mono` (`Parties.lean`) |
| P6, (S2.21) | `∂x*/∂t = -kγvD/κ`; tying amendments lowers mobilisation at once | `hasDerivAt_mobilisation_tied`, `mobilisation_falls_with_tying` |
| P8, (S2.22) | Conditioning adds the term `ω ∂T/∂ŷ` and nothing else; spreading a reward over more indicators lowers the weight of each | `conditioning_margin`, `weight_falls_with_indicators` |
| P9 | The electoral term vanishes for a mayor who cannot run again; the ban term is largest at the threshold and falls with the distance from it | `mei`, `mei_lame_duck`, `phi_le_phi_zero`, `phi_anti_abs`, `phi_le_decay`, `sanction_term_far` |
| P10, eq. (10), (S2.23) | The derivative (S2.23); implementation rises with the incentive at a falling rate; an executed ban lowers it to `1 - η(1 - c/2)exp(-sS/I* - θ/4)`; with `η = 0` it is one | `hasDerivAt_implQuality`, `implQuality_deriv_pos`, `implQuality_strictMono`, `implQuality_deriv_falls`, `implQuality_ban`, `implQuality_ban_lowers`, `implQuality_scenarioA` (`Implementation.lean`) |

`Basic.lean` holds small facts about division and two consequences of the mean value theorem used by the other
files.

## What is assumed rather than proved

* **The distribution of the noise.** The results on the probability of a sanction hold for any noise whose
  distribution function `F` has a density `f` (`F' = f`); the normal distribution, whose distribution function has
  the normal density as derivative, is one case. The facts that use the exact shape of the normal density (its
  peak `1/√(2π)` and its decay) are proved for that density itself, `phi`.
* **Covariances.** Centred, square-integrable random variables form a real inner product space whose inner
  product is the covariance; P1 and P4 are proved in any such space. That independent variables are uncorrelated
  (orthogonal) is a standard fact, used as the hypothesis of zero covariance.
* **Joint normality in P1.** That `E[θ | ŷ]` is linear in `ŷ` when `θ` and `ŷ` are jointly normal is a standard
  fact; the theorem `corr_function_le` takes its consequence, `cov(g, θ) = c cov(g, ŷ)` for every function `g` of
  `ŷ`, as a hypothesis.
* **The two formulas of contract theory**, (S2.7) and (S2.8), are taken from Holmström and Milgrom (1991,
  equation 7) and Baker (1992, equation 8); only the properties that Section S2.1 attributes to them are proved.
  The zero weight when an essential task cannot be measured (Holmström and Milgrom, 1991, Proposition 1) is cited,
  not proved.

Not formalised: P7, whose argument rests on evidence about voters; the comparison of costs in P5 (why recruitment
is the cheaper route); the career-incentive evidence of Bertrand et al. (2020) recalled in Section S2.1.

## Files

```
lean-toolchain        Lean version (v4.15.0)
lakefile.lean         project file; requires Mathlib v4.15.0
lake-manifest.json    exact revisions of Mathlib and of the packages it uses, written by the build
LRGProofs.lean        imports every file
LRGProofs/            Basic, Effort, Quadratic, Cosmetic, ContractTheory, Sanctions, Information, Money,
                      Parties, Clientelism, Implementation, Axioms
results/              build_log.txt (the build of 9 October 2026) and SHA256SUMS.txt (the files built)
```
