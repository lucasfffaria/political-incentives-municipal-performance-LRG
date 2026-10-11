import Mathlib

/-!
# What a sanction reveals about the mayor: (S2.14) and proposition P1

Centred, square-integrable random variables form a real inner product space in which the inner
product is the covariance and the norm is the standard deviation; uncorrelated variables (in
particular independent ones) are orthogonal. The results below are stated in any real inner
product space `E`. In them `θ` is the mayor's competence, `u` collects the place, the other terms
and the noise of the reported value, and `ŷ = λθ + u`.
-/

namespace LRG

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- The real inner product (the covariance, for centred random variables). -/
local notation "⟪" x ", " y "⟫" => @inner ℝ _ _ x y

/-- The covariance of the reported value with competence, when `u` is uncorrelated with `θ`:
`cov(λθ + u, θ) = λ var(θ)`. -/
theorem cov_reported_competence (lam : ℝ) (θ u : E) (hu : ⟪u, θ⟫ = 0) :
    ⟪lam • θ + u, θ⟫ = lam * ‖θ‖ ^ 2 := by
  rw [inner_add_left, real_inner_smul_left, hu, real_inner_self_eq_norm_sq, add_zero]

/-- (S2.14): `corr(ŷ, θ) = λ σ_θ / σ_ŷ`. -/
theorem corr_reported_competence (lam : ℝ) (θ u : E) (hu : ⟪u, θ⟫ = 0)
    (hθ : θ ≠ 0) (hy : lam • θ + u ≠ 0) :
    ⟪lam • θ + u, θ⟫ / (‖lam • θ + u‖ * ‖θ‖) = lam * ‖θ‖ / ‖lam • θ + u‖ := by
  rw [cov_reported_competence lam θ u hu]
  have h1 : ‖θ‖ ≠ 0 := norm_ne_zero_iff.mpr hθ
  have h2 : ‖lam • θ + u‖ ≠ 0 := norm_ne_zero_iff.mpr hy
  field_simp <;> ring

/-- P1: if the best prediction of `θ` from `ŷ` is linear, `E[θ | ŷ] = c ŷ` (as it is when `θ` and
`ŷ` are jointly normal), then every variable `g` that is a function of `ŷ` satisfies
`cov(g, θ) = c cov(g, ŷ)`, and no such variable (a sanction in particular) is more correlated
with `θ` than `ŷ` itself: `|corr(g, θ)| ≤ |corr(ŷ, θ)|`. The hypotheses `hy` and `hg` state the
property `cov(g, θ) = c cov(g, ŷ)` for `ŷ` and for `g`. -/
theorem corr_function_le (θ y g : E) (c : ℝ)
    (hy : ⟪y, θ⟫ = c * ⟪y, y⟫) (hg : ⟪g, θ⟫ = c * ⟪g, y⟫)
    (hθ : θ ≠ 0) (hy0 : y ≠ 0) (hg0 : g ≠ 0) :
    |⟪g, θ⟫| / (‖g‖ * ‖θ‖) ≤ |⟪y, θ⟫| / (‖y‖ * ‖θ‖) := by
  have hθn : 0 < ‖θ‖ := norm_pos_iff.mpr hθ
  have hyn : 0 < ‖y‖ := norm_pos_iff.mpr hy0
  have hgn : 0 < ‖g‖ := norm_pos_iff.mpr hg0
  have hθn' : ‖θ‖ ≠ 0 := hθn.ne'
  have hyn' : ‖y‖ ≠ 0 := hyn.ne'
  have hgn' : ‖g‖ ≠ 0 := hgn.ne'
  -- the right-hand side equals |c| ‖y‖ / ‖θ‖
  have hR : |⟪y, θ⟫| / (‖y‖ * ‖θ‖) = |c| * ‖y‖ / ‖θ‖ := by
    rw [hy, real_inner_self_eq_norm_sq, abs_mul, abs_of_nonneg (sq_nonneg ‖y‖)]
    field_simp <;> ring
  -- the left-hand side is at most |c| ‖y‖ / ‖θ‖, by the Cauchy-Schwarz inequality
  have hCS : |⟪g, y⟫| ≤ ‖g‖ * ‖y‖ := abs_real_inner_le_norm g y
  have hL : |⟪g, θ⟫| ≤ |c| * (‖g‖ * ‖y‖) := by
    rw [hg, abs_mul]
    exact mul_le_mul_of_nonneg_left hCS (abs_nonneg c)
  have hden : 0 < ‖g‖ * ‖θ‖ := mul_pos hgn hθn
  have h1 : |⟪g, θ⟫| / (‖g‖ * ‖θ‖) ≤ |c| * (‖g‖ * ‖y‖) / (‖g‖ * ‖θ‖) := by
    have h := mul_le_mul_of_nonneg_right hL (inv_nonneg.mpr hden.le)
    simpa only [div_eq_mul_inv] using h
  have h2 : |c| * (‖g‖ * ‖y‖) / (‖g‖ * ‖θ‖) = |c| * ‖y‖ / ‖θ‖ := by
    field_simp <;> ring
  rw [hR]
  linarith

end LRG
