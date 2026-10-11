import Mathlib

/-!
# Implementation: equation (10) of the article, (S2.23) and proposition P10

Money and assistance deliver only if the programmes they fund are carried out as designed. The
realised share of their potential benefit, the implementation quality, depends on the mayor's
total incentive `I`, on supervision `S`, on capacity `c` and on competence `θ` (equation 10);
`η ∈ [0, 1]` measures how much implementation depends on incentives and `I*` is a scale.
-/

namespace LRG

/-- Implementation quality, equation (10) of the article:
`ι = 1 - η (1 - c/2) exp(-(I + sS)/I*) exp(-θ/4)`. -/
noncomputable def implQuality (η c θ s S Istar I : ℝ) : ℝ :=
  1 - η * (1 - c / 2) * Real.exp (-(I + s * S) / Istar) * Real.exp (-θ / 4)

/-- (S2.23): the derivative of implementation quality with respect to the total incentive. -/
theorem hasDerivAt_implQuality (η c θ s S Istar I : ℝ) :
    HasDerivAt (fun J => implQuality η c θ s S Istar J)
      (η / Istar * (1 - c / 2) * Real.exp (-(I + s * S) / Istar) * Real.exp (-θ / 4)) I := by
  have hid : HasDerivAt (fun J : ℝ => J) 1 I := hasDerivAt_id I
  have h1 : HasDerivAt (fun J : ℝ => -(J + s * S) / Istar) (-1 / Istar) I :=
    ((hid.add_const (s * S)).neg).div_const Istar
  have h2 : HasDerivAt (fun J : ℝ => Real.exp (-(J + s * S) / Istar))
      (Real.exp (-(I + s * S) / Istar) * (-1 / Istar)) I := h1.exp
  have h3 := ((h2.const_mul (η * (1 - c / 2))).mul_const (Real.exp (-θ / 4))).const_sub 1
  unfold implQuality
  convert h3 using 1
  ring

/-- The derivative (S2.23) is positive when implementation depends on incentives (`η > 0`) and
capacity is below two (it is a share between zero and one). -/
theorem implQuality_deriv_pos {η c θ s S Istar I : ℝ} (hη : 0 < η) (hc : c < 2)
    (hI : 0 < Istar) :
    0 < η / Istar * (1 - c / 2) * Real.exp (-(I + s * S) / Istar) * Real.exp (-θ / 4) := by
  have h1 : 0 < 1 - c / 2 := by linarith
  exact mul_pos (mul_pos (mul_pos (div_pos hη hI) h1) (Real.exp_pos _)) (Real.exp_pos _)

/-- P10: implementation quality rises strictly with the total incentive, so the threat of a ban,
which adds to the incentive, raises cooperation like any other incentive. -/
theorem implQuality_strictMono {η c θ s S Istar : ℝ} (hη : 0 < η) (hc : c < 2) (hI : 0 < Istar) :
    StrictMono (fun J => implQuality η c θ s S Istar J) := by
  apply strictMono_of_deriv_pos
  intro J
  rw [(hasDerivAt_implQuality η c θ s S Istar J).deriv]
  exact implQuality_deriv_pos hη hc hI

/-- P10: the gain from a higher incentive is largest where the incentive is small: the derivative
(S2.23) falls as `I` rises. -/
theorem implQuality_deriv_falls {η c θ s S Istar I J : ℝ} (hη : 0 < η) (hc : c < 2)
    (hI : 0 < Istar) (hIJ : I < J) :
    η / Istar * (1 - c / 2) * Real.exp (-(J + s * S) / Istar) * Real.exp (-θ / 4)
      < η / Istar * (1 - c / 2) * Real.exp (-(I + s * S) / Istar) * Real.exp (-θ / 4) := by
  have hexp : Real.exp (-(J + s * S) / Istar) < Real.exp (-(I + s * S) / Istar) := by
    rw [Real.exp_lt_exp]
    have e : -(I + s * S) / Istar - -(J + s * S) / Istar = (J - I) / Istar := by ring
    have hpos : 0 < (J - I) / Istar := div_pos (by linarith) hI
    linarith
  have hk : 0 < η / Istar * (1 - c / 2) := mul_pos (div_pos hη hI) (by linarith)
  have h4 := mul_lt_mul_of_pos_left hexp hk
  exact mul_lt_mul_of_pos_right h4 (Real.exp_pos _)

/-- P10: a ban that is executed sets the banned mayor's incentive to zero, which lowers
implementation quality to `1 - η (1 - c/2) exp(-sS/I* - θ/4)`. -/
theorem implQuality_ban (η c θ s S Istar : ℝ) :
    implQuality η c θ s S Istar 0
      = 1 - η * (1 - c / 2) * Real.exp (-(s * S) / Istar - θ / 4) := by
  unfold implQuality
  rw [show -(s * S) / Istar - θ / 4 = -(0 + s * S) / Istar + -θ / 4 by ring, Real.exp_add]
  ring

/-- P10: with a positive incentive, an executed ban lowers implementation quality. -/
theorem implQuality_ban_lowers {η c θ s S Istar I : ℝ} (hη : 0 < η) (hc : c < 2)
    (hIs : 0 < Istar) (hI : 0 < I) :
    implQuality η c θ s S Istar 0 < implQuality η c θ s S Istar I :=
  implQuality_strictMono hη hc hIs hI

/-- Scenario A of the article (`η = 0`): implementation does not depend on incentives at all. -/
theorem implQuality_scenarioA (c θ s S Istar I : ℝ) : implQuality 0 c θ s S Istar I = 1 := by
  unfold implQuality
  simp

end LRG
