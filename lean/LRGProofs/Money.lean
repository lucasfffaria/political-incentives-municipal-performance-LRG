import Mathlib
import LRGProofs.Basic

/-!
# What the money rewards: (S2.19), (S2.22) and propositions P4 and P8

As in `Information.lean`, centred square-integrable random variables are elements of a real inner
product space in which the inner product is the covariance.
-/

namespace LRG

section Covariance

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- The real inner product (the covariance, for centred random variables). -/
local notation "⟪" x ", " y "⟫" => @inner ℝ _ _ x y

/-- (S2.19), P4: write the reported value in two consecutive years as the place `s` plus the
mayor `m` plus yearly noise, with the noise of one year uncorrelated with that of the next. The
change in the reported value then covaries negatively with last year's noise:
`cov(Δŷ, ε_{t-1}) = -var(ε_{t-1})`, so a transfer paid on raw changes pays for the rebound that
follows bad luck. -/
theorem cov_change_lagged_noise (s m e₁ e₀ : E) (h : ⟪e₁, e₀⟫ = 0) :
    ⟪(s + m + e₁) - (s + m + e₀), e₀⟫ = -‖e₀‖ ^ 2 := by
  have hd : (s + m + e₁) - (s + m + e₀) = e₁ - e₀ := by abel
  rw [hd, inner_sub_left, h, real_inner_self_eq_norm_sq]
  ring

end Covariance

/-- P4: when the value of money is concave in coverage, moving an amount `m ≥ 0` from a
municipality at level `x` to one at a higher level `y` adds less where it arrives than it
subtracts where it leaves, so the sum of the two values does not rise. -/
theorem concave_transfer {h : ℝ → ℝ} (hc : ConcaveOn ℝ Set.univ h) {x y m : ℝ}
    (hxy : x ≤ y) (hm : 0 ≤ m) : h (x - m) + h (y + m) ≤ h x + h y := by
  rcases hm.eq_or_lt with h0 | hpos
  · subst h0
    simp
  · have hD : 0 < y - x + 2 * m := by linarith
    have hDne : y - x + 2 * m ≠ 0 := hD.ne'
    have hα0 : 0 ≤ (y + m - x) / (y - x + 2 * m) := div_nonneg (by linarith) hD.le
    have hβ0 : 0 ≤ m / (y - x + 2 * m) := div_nonneg hm hD.le
    have hsum : (y + m - x) / (y - x + 2 * m) + m / (y - x + 2 * m) = 1 := by
      field_simp <;> ring
    have hsum' : m / (y - x + 2 * m) + (y + m - x) / (y - x + 2 * m) = 1 := by
      linarith
    -- `x` and `y` are convex combinations of `x - m` and `y + m`
    have hx : (y + m - x) / (y - x + 2 * m) * (x - m) + m / (y - x + 2 * m) * (y + m) = x := by
      field_simp <;> ring
    have hy : m / (y - x + 2 * m) * (x - m) + (y + m - x) / (y - x + 2 * m) * (y + m) = y := by
      field_simp <;> ring
    have h1 := hc.2 (Set.mem_univ (x - m)) (Set.mem_univ (y + m)) hα0 hβ0 hsum
    have h2 := hc.2 (Set.mem_univ (x - m)) (Set.mem_univ (y + m)) hβ0 hα0 hsum'
    simp only [smul_eq_mul] at h1 h2
    rw [hx] at h1
    rw [hy] at h2
    have e1 : h (x - m) = (y + m - x) / (y - x + 2 * m) * h (x - m)
        + m / (y - x + 2 * m) * h (x - m) := by
      rw [← add_mul, hsum, one_mul]
    have e2 : h (y + m) = (y + m - x) / (y - x + 2 * m) * h (y + m)
        + m / (y - x + 2 * m) * h (y + m) := by
      rw [← add_mul, hsum, one_mul]
    linarith

/-- (S2.22), P8: a results-based transfer `T(ŷ)` enters the marginal expected incentive through
`ω ∂T/∂ŷ`, whereas an unconditional transfer of the same expected value contributes nothing to
it; both raise expected utility by `ω` times their common expected value. -/
theorem conditioning_margin {T : ℝ → ℝ} {T' ω T₀ y : ℝ} (hT : HasDerivAt T T' y) :
    HasDerivAt (fun z => ω * T z) (ω * T') y ∧ HasDerivAt (fun _ : ℝ => ω * T₀) 0 y :=
  ⟨hT.const_mul ω, hasDerivAt_const y (ω * T₀)⟩

/-- P8: a reward `W > 0` spread equally over `K` indicators gives each indicator the weight
`W/K`, which falls as the number of indicators grows. -/
theorem weight_falls_with_indicators {W : ℝ} (hW : 0 < W) {K₁ K₂ : ℕ} (h1 : 0 < K₁)
    (h12 : K₁ < K₂) : W / (K₂ : ℝ) < W / (K₁ : ℝ) := by
  have hK1 : (0 : ℝ) < K₁ := by exact_mod_cast h1
  have hK12 : (K₁ : ℝ) < K₂ := by exact_mod_cast h12
  exact aux_div_lt_div_left hW hK1 hK12

end LRG
