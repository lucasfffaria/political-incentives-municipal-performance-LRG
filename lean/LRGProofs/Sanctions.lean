import Mathlib
import LRGProofs.Basic

/-!
# Sanctions: (S2.9), (S2.10), (S2.12), (S2.13), (S2.15) to (S2.17); propositions P1, P2 and P9

A sanction follows when the reported value falls below a threshold `τ`. With expected reported
value `s + λθ + r` (the place, the mayor's contribution and the rest) and noise of scale `σ`, its
probability is `F((τ - (s + λθ + r))/σ)`, where `F` is the cumulative distribution function of the
standardised noise (S2.9 and S2.10). The results on derivatives hold for any noise whose
distribution function `F` has a density `f`, that is `F' = f`; for normal noise `F = Φ` and
`f = φ`, the standard normal density defined below. The results that use the exact shape of `φ`
are stated for `φ` itself.
-/

namespace LRG

/-! ## The standard normal density -/

/-- The constant `1/√(2π)`. -/
noncomputable def normConst : ℝ := (Real.sqrt (2 * Real.pi))⁻¹

theorem normConst_pos : 0 < normConst := by
  unfold normConst
  exact inv_pos.mpr (Real.sqrt_pos.mpr (by positivity))

/-- The standard normal density `φ(z) = exp(-z²/2)/√(2π)`. -/
noncomputable def phi (z : ℝ) : ℝ := normConst * Real.exp (-z ^ 2 / 2)

theorem phi_pos (z : ℝ) : 0 < phi z := mul_pos normConst_pos (Real.exp_pos _)

theorem phi_zero : phi 0 = normConst := by
  unfold phi
  simp

/-- The density is largest at zero, that is, at the threshold. -/
theorem phi_le_phi_zero (z : ℝ) : phi z ≤ phi 0 := by
  have h : Real.exp (-z ^ 2 / 2) ≤ Real.exp (-(0 : ℝ) ^ 2 / 2) := by
    rw [Real.exp_le_exp]
    nlinarith [sq_nonneg z]
  unfold phi
  exact mul_le_mul_of_nonneg_left h normConst_pos.le

/-- The density falls with the distance from the threshold. -/
theorem phi_anti_abs {z₁ z₂ : ℝ} (h : |z₁| ≤ |z₂|) : phi z₂ ≤ phi z₁ := by
  have hsq : z₁ ^ 2 ≤ z₂ ^ 2 := by
    have h0 : 0 ≤ |z₁| := abs_nonneg z₁
    have hm : |z₁| * |z₁| ≤ |z₂| * |z₂| := mul_le_mul h h h0 (le_trans h0 h)
    nlinarith [sq_abs z₁, sq_abs z₂]
  have hexp : Real.exp (-z₂ ^ 2 / 2) ≤ Real.exp (-z₁ ^ 2 / 2) := by
    rw [Real.exp_le_exp]
    linarith
  unfold phi
  exact mul_le_mul_of_nonneg_left hexp normConst_pos.le

/-- Far from the threshold the density vanishes: `φ(z) ≤ (1/√(2π)) / (1 + z²/2)`. -/
theorem phi_le_decay (z : ℝ) : phi z ≤ normConst / (1 + z ^ 2 / 2) := by
  have hpos : 0 < 1 + z ^ 2 / 2 := by positivity
  have hpos' : 1 + z ^ 2 / 2 ≠ 0 := hpos.ne'
  have h2 : (2 : ℝ) + z ^ 2 ≠ 0 := by positivity
  have hE : 0 < Real.exp (z ^ 2 / 2) := Real.exp_pos _
  have hE' : Real.exp (z ^ 2 / 2) ≠ 0 := hE.ne'
  have hexp : 1 + z ^ 2 / 2 ≤ Real.exp (z ^ 2 / 2) := by
    have := Real.add_one_le_exp (z ^ 2 / 2)
    linarith
  have hneg : Real.exp (-z ^ 2 / 2) = (Real.exp (z ^ 2 / 2))⁻¹ := by
    rw [← Real.exp_neg]
    congr 1
    ring
  have key : (Real.exp (z ^ 2 / 2))⁻¹ ≤ 1 / (1 + z ^ 2 / 2) := by
    have id1 : 1 / (1 + z ^ 2 / 2) - (Real.exp (z ^ 2 / 2))⁻¹
        = (Real.exp (z ^ 2 / 2) - (1 + z ^ 2 / 2)) / ((1 + z ^ 2 / 2) * Real.exp (z ^ 2 / 2)) := by
      field_simp <;> ring
    have hnn : 0 ≤ (Real.exp (z ^ 2 / 2) - (1 + z ^ 2 / 2)) / ((1 + z ^ 2 / 2) * Real.exp (z ^ 2 / 2)) :=
      div_nonneg (by linarith) (mul_pos hpos hE).le
    linarith
  unfold phi
  rw [hneg]
  calc normConst * (Real.exp (z ^ 2 / 2))⁻¹ ≤ normConst * (1 / (1 + z ^ 2 / 2)) :=
        mul_le_mul_of_nonneg_left key normConst_pos.le
    _ = normConst / (1 + z ^ 2 / 2) := by ring

/-! ## The probability of a sanction and its derivatives: (S2.9), (S2.10), (S2.12), (S2.13), P1 -/

/-- (S2.9)-(S2.10): the probability of a sanction, `F(z)` with
`z = (τ - (s + λθ + r))/σ`. -/
noncomputable def sanctionProb (F : ℝ → ℝ) (τ σ s lam θ r : ℝ) : ℝ := F ((τ - (s + lam * θ + r)) / σ)

/-- (S2.12): the response of the probability of a sanction to the place `s`. -/
theorem hasDerivAt_sanctionProb_place {F f : ℝ → ℝ} (hF : ∀ z, HasDerivAt F (f z) z)
    (τ σ lam θ r s : ℝ) :
    HasDerivAt (fun x => sanctionProb F τ σ x lam θ r)
      (-(f ((τ - (s + lam * θ + r)) / σ)) / σ) s := by
  have h1 : HasDerivAt (fun x : ℝ => x + lam * θ + r) 1 s :=
    ((hasDerivAt_id s).add_const (lam * θ)).add_const r
  have hin : HasDerivAt (fun x : ℝ => (τ - (x + lam * θ + r)) / σ) (-1 / σ) s :=
    (h1.const_sub τ).div_const σ
  have h : HasDerivAt (fun x => F ((τ - (x + lam * θ + r)) / σ))
      (f ((τ - (s + lam * θ + r)) / σ) * (-1 / σ)) s :=
    (hF ((τ - (s + lam * θ + r)) / σ)).comp s hin
  unfold sanctionProb
  convert h using 1
  ring

/-- (S2.13): the response of the probability of a sanction to the mayor's competence `θ`. -/
theorem hasDerivAt_sanctionProb_mayor {F f : ℝ → ℝ} (hF : ∀ z, HasDerivAt F (f z) z)
    (τ σ s lam r θ : ℝ) :
    HasDerivAt (fun t => sanctionProb F τ σ s lam t r)
      (-(lam * f ((τ - (s + lam * θ + r)) / σ)) / σ) θ := by
  have hid : HasDerivAt (fun t : ℝ => t) 1 θ := hasDerivAt_id θ
  have h1 : HasDerivAt (fun t : ℝ => s + lam * t + r) (lam * 1) θ :=
    ((hid.const_mul lam).const_add s).add_const r
  have hin : HasDerivAt (fun t : ℝ => (τ - (s + lam * t + r)) / σ) (-(lam * 1) / σ) θ :=
    (h1.const_sub τ).div_const σ
  have h : HasDerivAt (fun t => F ((τ - (s + lam * t + r)) / σ))
      (f ((τ - (s + lam * θ + r)) / σ) * (-(lam * 1) / σ)) θ :=
    (hF ((τ - (s + lam * θ + r)) / σ)).comp θ hin
  unfold sanctionProb
  convert h using 1
  ring

/-- P1: per unit of their contribution to the reported value, the place and the mayor move the
probability of a sanction by the same factor `f(z)/σ`; the mayor's contribution is `λ` per unit
of competence. -/
theorem sanction_response_ratio (lam fz σ : ℝ) : -(lam * fz) / σ = lam * (-fz / σ) := by
  ring

/-! ## Noise: (S2.15), (S2.16), (S2.17), P2 -/

/-- (S2.15): at the threshold the sanction term of the marginal expected incentive equals
`L / (√(2π) σ)`. -/
theorem sanction_term_peak (L σ : ℝ) : L * phi 0 / σ = L / (Real.sqrt (2 * Real.pi) * σ) := by
  rw [phi_zero]
  unfold normConst
  ring

/-- The sanction term `L φ(z)/σ` is largest at the threshold. -/
theorem sanction_term_le_peak {L σ : ℝ} (hL : 0 ≤ L) (hσ : 0 < σ) (z : ℝ) :
    L * phi z / σ ≤ L * phi 0 / σ :=
  aux_div_le_div_right (mul_le_mul_of_nonneg_left (phi_le_phi_zero z) hL) hσ

/-- P2: the peak of the sanction term falls as the noise rises. -/
theorem sanction_term_peak_falls_with_noise {L σ₁ σ₂ : ℝ} (hL : 0 < L) (h1 : 0 < σ₁)
    (h12 : σ₁ < σ₂) : L * phi 0 / σ₂ < L * phi 0 / σ₁ :=
  aux_div_lt_div_left (mul_pos hL (phi_pos 0)) h1 h12

/-- `-Δ/σ` rises with `σ` when `Δ > 0`. -/
theorem neg_div_le_neg_div {D σ₁ σ₂ : ℝ} (hD : 0 < D) (h1 : 0 < σ₁) (h12 : σ₁ ≤ σ₂) :
    -D / σ₁ ≤ -D / σ₂ := by
  have h2 : 0 < σ₂ := lt_of_lt_of_le h1 h12
  have h1' : σ₁ ≠ 0 := h1.ne'
  have h2' : σ₂ ≠ 0 := h2.ne'
  have e : -D / σ₂ - -D / σ₁ = D * (σ₂ - σ₁) / (σ₁ * σ₂) := by
    field_simp <;> ring
  have hnn : 0 ≤ D * (σ₂ - σ₁) / (σ₁ * σ₂) :=
    div_nonneg (mul_nonneg hD.le (by linarith)) (mul_pos h1 h2).le
  linarith

/-- `-Δ/σ` rises strictly with `σ` when `Δ > 0`. -/
theorem neg_div_lt_neg_div {D σ₁ σ₂ : ℝ} (hD : 0 < D) (h1 : 0 < σ₁) (h12 : σ₁ < σ₂) :
    -D / σ₁ < -D / σ₂ := by
  have h2 : 0 < σ₂ := lt_trans h1 h12
  have h1' : σ₁ ≠ 0 := h1.ne'
  have h2' : σ₂ ≠ 0 := h2.ne'
  have e : -D / σ₂ - -D / σ₁ = D * (σ₂ - σ₁) / (σ₁ * σ₂) := by
    field_simp <;> ring
  have hpos : 0 < D * (σ₂ - σ₁) / (σ₁ * σ₂) :=
    div_pos (mul_pos hD (by linarith)) (mul_pos h1 h2)
  linarith

/-- (S2.16): a mayor whose true performance is `Δ > 0` above the threshold is sanctioned by
mistake with probability `F(-Δ/σ)`, which does not fall as the noise `σ` rises, whatever the
(monotone) distribution function `F` of the standardised noise. -/
theorem misclassification_mono {F : ℝ → ℝ} (hF : Monotone F) {D σ₁ σ₂ : ℝ}
    (hD : 0 < D) (h1 : 0 < σ₁) (h12 : σ₁ ≤ σ₂) : F (-D / σ₁) ≤ F (-D / σ₂) :=
  hF (neg_div_le_neg_div hD h1 h12)

/-- A distribution function with a positive density is strictly increasing. -/
theorem strictMono_of_density {F f : ℝ → ℝ} (hF : ∀ z, HasDerivAt F (f z) z)
    (hf : ∀ z, 0 < f z) : StrictMono F := by
  apply strictMono_of_deriv_pos
  intro z
  rw [(hF z).deriv]
  exact hf z

/-- (S2.16), strict form: with a positive density (normal noise in particular) the probability
of a mistaken sanction rises strictly with the noise. -/
theorem misclassification_strictMono {F f : ℝ → ℝ} (hF : ∀ z, HasDerivAt F (f z) z)
    (hf : ∀ z, 0 < f z) {D σ₁ σ₂ : ℝ} (hD : 0 < D) (h1 : 0 < σ₁) (h12 : σ₁ < σ₂) :
    F (-D / σ₁) < F (-D / σ₂) :=
  strictMono_of_density hF hf (neg_div_lt_neg_div hD h1 h12)

/-- (S2.17): with `K` independent tests, each failed with probability `p`, the probability of
failing at least one, `1 - (1 - p)^K`, does not fall as tests are added. -/
theorem fail_at_least_one_mono {p : ℝ} (hp0 : 0 ≤ p) (hp1 : p ≤ 1) (K : ℕ) :
    1 - (1 - p) ^ K ≤ 1 - (1 - p) ^ (K + 1) := by
  have h0 : 0 ≤ 1 - p := by linarith
  have hpow : 0 ≤ (1 - p) ^ K := pow_nonneg h0 K
  have e : (1 - p) ^ (K + 1) = (1 - p) ^ K * (1 - p) := by ring
  rw [e]
  nlinarith [mul_nonneg hpow hp0]

/-- (S2.17): the probability of failing at least one of `K` tests tends to one as `K` grows. -/
theorem fail_at_least_one_tendsto {p : ℝ} (hp0 : 0 < p) (hp1 : p ≤ 1) :
    Filter.Tendsto (fun K : ℕ => 1 - (1 - p) ^ K) Filter.atTop (nhds 1) := by
  have h : Filter.Tendsto (fun K : ℕ => (1 - p) ^ K) Filter.atTop (nhds 0) :=
    tendsto_pow_atTop_nhds_zero_of_lt_one (by linarith) (by linarith)
  have hc : Filter.Tendsto (fun _ : ℕ => (1 : ℝ)) Filter.atTop (nhds 1) := tendsto_const_nhds
  have := hc.sub h
  simpa using this

/-! ## The marginal expected incentive and career sanctions: equation (4), P9 -/

/-- The marginal expected incentive, equation (4) of the article: the electoral term
`R ∂π/∂ŷ`, the money term `ω ∂T/∂ŷ`, the party term `ψ ∂F/∂ŷ`, a personal bonus `b ∂B/∂ŷ` and
the sanction term `L φ(z)/σ`. -/
noncomputable def mei (R dπ ω dT ψ dF b dB L z σ : ℝ) : ℝ :=
  R * dπ + ω * dT + ψ * dF + b * dB + L * phi z / σ

/-- P9: for a mayor who cannot run again (`R = 0`) the electoral term disappears. -/
theorem mei_lame_duck (dπ ω dT ψ dF b dB L z σ : ℝ) :
    mei 0 dπ ω dT ψ dF b dB L z σ = ω * dT + ψ * dF + b * dB + L * phi z / σ := by
  unfold mei
  ring

/-- P9: the sanction term is at most `L/(√(2π) σ)` at any distance from the threshold, and at a
distance `z` it is at most that peak divided by `1 + z²/2`. -/
theorem sanction_term_far {L σ : ℝ} (hL : 0 ≤ L) (hσ : 0 < σ) (z : ℝ) :
    L * phi z / σ ≤ L * phi 0 / σ / (1 + z ^ 2 / 2) := by
  have hpos : 0 < 1 + z ^ 2 / 2 := by positivity
  have h := phi_le_decay z
  rw [← phi_zero] at h
  have h1 : L * phi z ≤ L * (phi 0 / (1 + z ^ 2 / 2)) := mul_le_mul_of_nonneg_left h hL
  have h2 : L * phi z / σ ≤ L * (phi 0 / (1 + z ^ 2 / 2)) / σ := aux_div_le_div_right h1 hσ
  have e : L * (phi 0 / (1 + z ^ 2 / 2)) / σ = L * phi 0 / σ / (1 + z ^ 2 / 2) := by ring
  linarith

end LRG
