import Mathlib
import LRGProofs.Basic

/-!
# Two results from contract theory, as written in (S2.7) and (S2.8)

Section S2.1 of the Supplementary Material recalls two formulas from the literature: the optimal
weight on a measured task when a second task cannot be measured (Holmström and Milgrom, 1991,
equation 7) and the optimal piece rate when the measure responds to effort differently from
welfare (Baker, 1992, equation 8). The formulas are cited, not derived, here; this file proves the
properties that the text attributes to them, and shows with explicit numbers where a property
needs a condition.
-/

namespace LRG

/-! ## (S2.7): the weight on the measured task -/

/-- The optimal weight on the measured task, (S2.7): `B₁`, `B₂` are the marginal values of the
two tasks, `C₁₁`, `C₁₂`, `C₂₂` the second derivatives of the agent's cost, `r` the agent's risk
aversion and `s2 = σ₁²` the noise of the measure. -/
noncomputable def hmWeight (B₁ B₂ C₁₁ C₁₂ C₂₂ r s2 : ℝ) : ℝ :=
  (B₁ - B₂ * C₁₂ / C₂₂) / (1 + r * s2 * (C₁₁ - C₁₂ ^ 2 / C₂₂))

/-- The weight falls with the noise of the measure, when the measured task is worth rewarding
(positive numerator), the agent is risk-averse and the cost is convex
(`C₁₁ - C₁₂²/C₂₂ > 0`). -/
theorem hmWeight_falls_with_noise {B₁ B₂ C₁₁ C₁₂ C₂₂ r s s' : ℝ}
    (hN : 0 < B₁ - B₂ * C₁₂ / C₂₂) (hK : 0 < C₁₁ - C₁₂ ^ 2 / C₂₂) (hr : 0 < r)
    (hs : 0 ≤ s) (hss : s < s') :
    hmWeight B₁ B₂ C₁₁ C₁₂ C₂₂ r s' < hmWeight B₁ B₂ C₁₁ C₁₂ C₂₂ r s := by
  unfold hmWeight
  apply aux_div_lt_div_left hN
  · have : 0 ≤ r * s * (C₁₁ - C₁₂ ^ 2 / C₂₂) := mul_nonneg (mul_nonneg hr.le hs) hK.le
    linarith
  · have h1 : r * s < r * s' := mul_lt_mul_of_pos_left hss hr
    have h2 : r * s * (C₁₁ - C₁₂ ^ 2 / C₂₂) < r * s' * (C₁₁ - C₁₂ ^ 2 / C₂₂) :=
      mul_lt_mul_of_pos_right h1 hK
    linarith

/-- For a risk-neutral agent the weight is the numerator `B₁ - B₂ C₁₂/C₂₂`. -/
theorem hmWeight_risk_neutral (B₁ B₂ C₁₁ C₁₂ C₂₂ s2 : ℝ) :
    hmWeight B₁ B₂ C₁₁ C₁₂ C₂₂ 0 s2 = B₁ - B₂ * C₁₂ / C₂₂ := by
  unfold hmWeight
  simp

/-- The numerator falls with the substitution `C₁₂` between the tasks whenever the unmeasured task
is valuable (`B₂ > 0`); for a risk-neutral agent, therefore, the weight itself falls with the
substitution. -/
theorem hm_numerator_falls_with_substitution {B₁ B₂ C₂₂ c c' : ℝ} (hB : 0 < B₂) (hC : 0 < C₂₂)
    (hcc : c < c') : B₁ - B₂ * c' / C₂₂ < B₁ - B₂ * c / C₂₂ := by
  have e : B₂ * c' / C₂₂ - B₂ * c / C₂₂ = B₂ * (c' - c) / C₂₂ := by ring
  have hpos : 0 < B₂ * (c' - c) / C₂₂ := div_pos (mul_pos hB (by linarith)) hC
  linarith

/-- With a risk-averse agent the weight need not fall with the substitution: for `B₁ = 1`,
`B₂ = 1/10`, `C₁₁ = C₂₂ = 1` and `r σ₁² = 1`, it rises from `1/2` at `C₁₂ = 0` to `19/35` at
`C₁₂ = 1/2`. This is why Section S2.1 states the effect of substitution for a risk-neutral
agent only. -/
theorem hmWeight_can_rise_with_substitution :
    hmWeight 1 (1 / 10) 1 0 1 1 1 < hmWeight 1 (1 / 10) 1 (1 / 2) 1 1 1 := by
  unfold hmWeight
  norm_num

/-! ## (S2.8): the optimal piece rate when the measure is distorted -/

/-- The optimal piece rate of (S2.8) for a risk-neutral agent, when the effect of effort on
welfare and on the measure have mean one, standard deviations `σV` and `σP`, and correlation
`ρ`. -/
noncomputable def bakerRate (ρ σV σP : ℝ) : ℝ := (ρ * σV * σP + 1) / (σP ^ 2 + 1)

/-- The rate is below one exactly when `ρ σV < σP`. -/
theorem bakerRate_lt_one_iff {ρ σV σP : ℝ} (hP : 0 < σP) :
    bakerRate ρ σV σP < 1 ↔ ρ * σV < σP := by
  have hd : 0 < σP ^ 2 + 1 := by positivity
  unfold bakerRate
  rw [aux_div_lt_one_iff hd]
  constructor
  · intro h
    by_contra hneg
    push_neg at hneg
    nlinarith
  · intro h
    nlinarith

/-- When welfare and the measure respond to effort with the same dispersion, the rate is below
one unless the two responses are perfectly correlated. -/
theorem bakerRate_equal_dispersion {ρ σ : ℝ} (hσ : 0 < σ) :
    bakerRate ρ σ σ < 1 ↔ ρ < 1 := by
  rw [bakerRate_lt_one_iff hσ]
  constructor
  · intro h
    by_contra hneg
    push_neg at hneg
    nlinarith
  · intro h
    nlinarith

/-- With perfectly correlated responses of equal dispersion the rate is one. -/
theorem bakerRate_aligned (σ : ℝ) : bakerRate 1 σ σ = 1 := by
  have hd : σ ^ 2 + 1 ≠ 0 := by positivity
  unfold bakerRate
  rw [div_eq_one_iff_eq hd]
  ring

/-- Without equal dispersion the rate can exceed one even with perfect correlation: with
`σV = 2`, `σP = 1` and `ρ = 1` it is `3/2`. This is why Section S2.1 states the condition
`ρ σV < σP`. -/
theorem bakerRate_can_exceed_one : 1 < bakerRate 1 2 1 := by
  unfold bakerRate
  norm_num

end LRG
