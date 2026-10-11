import Mathlib
import LRGProofs.Quadratic

/-!
# Clientelism: (S2.11), (S2.21) and proposition P6

Re-election responds to clientelist mobilisation `x` with a slope `γ v D`, which grows with the
vulnerability of voters `v` and with the discretionary money `D` that the mayor controls; tying a
share `t` of amendments to programmes leaves `(1 - t) D` discretionary. With value of office `k`
and a quadratic cost `κ x²/2`, the mayor's payoff from mobilisation is
`k γ v (1 - t) D x - κ x²/2`.
-/

namespace LRG

/-- (S2.11): the optimal mobilisation, `x* = k γ v (1 - t) D / κ`, proportional to the
vulnerability of voters, to the discretionary money and to the share of amendments left
untied. -/
noncomputable def mobilisation (k γ v t D κ : ℝ) : ℝ := k * γ * v * (1 - t) * D / κ

/-- (S2.11): `x*` maximises the mayor's payoff from mobilisation. -/
theorem mobilisation_optimal {k γ v t D κ : ℝ} (hκ : 0 < κ) (x : ℝ) :
    k * γ * v * (1 - t) * D * x - κ * x ^ 2 / 2
      ≤ k * γ * v * (1 - t) * D * mobilisation k γ v t D κ
        - κ * mobilisation k γ v t D κ ^ 2 / 2 := by
  unfold mobilisation
  exact quadratic_argmax hκ x

/-- (S2.21): the response of mobilisation to the share of amendments tied to programmes,
`∂x*/∂t = -k γ v D / κ`. -/
theorem hasDerivAt_mobilisation_tied (k γ v D κ t : ℝ) :
    HasDerivAt (fun t => mobilisation k γ v t D κ) (-(k * γ * v * D) / κ) t := by
  have hid : HasDerivAt (fun s : ℝ => s) 1 t := hasDerivAt_id t
  have h : HasDerivAt (fun s : ℝ => k * γ * v * (1 - s) * D / κ) (k * γ * v * (-1) * D / κ) t :=
    (((hid.const_sub 1).const_mul (k * γ * v)).mul_const D).div_const κ
  unfold mobilisation
  convert h using 1
  ring

/-- P6: tying amendments reduces mobilisation at once, in proportion to the discretionary money
removed. -/
theorem mobilisation_falls_with_tying {k γ v D κ t₁ t₂ : ℝ} (hpos : 0 < k * γ * v * D)
    (hκ : 0 < κ) (h12 : t₁ < t₂) : mobilisation k γ v t₂ D κ < mobilisation k γ v t₁ D κ := by
  unfold mobilisation
  have e : k * γ * v * (1 - t₁) * D / κ - k * γ * v * (1 - t₂) * D / κ
      = k * γ * v * D * (t₂ - t₁) / κ := by ring
  have hgap : 0 < k * γ * v * D * (t₂ - t₁) / κ := div_pos (mul_pos hpos (by linarith)) hκ
  linarith

end LRG
