import Mathlib
import LRGProofs.Basic

/-!
# The cosmetic share of a measured gain: (S2.4) to (S2.6) and (S2.18), proposition P3

An incentive raises true quality through effort, by `c (1 + φθ) a` (equation 8 of the article),
and the reported number through manipulation, by `I/κ` (equation 9). The cosmetic share is the
part of the measured gain that comes from manipulation. Here `m = 1 + φθ` is the mayor's
competence multiplier and `c` the administrative capacity.
-/

namespace LRG

/-- The algebra shared by (S2.6) and (S2.18): `(b/κ) / (q b + b/κ) = 1/(1 + q κ)`. -/
theorem share_identity {q κ b : ℝ} (hκ : 0 < κ) (hb : 0 < b) (hq : 0 ≤ q) :
    (b / κ) / (q * b + b / κ) = 1 / (1 + q * κ) := by
  have hκ' : κ ≠ 0 := hκ.ne'
  have hE : 0 < 1 + q * κ := by nlinarith [mul_nonneg hq hκ.le]
  have hden : q * b + b / κ = b * (1 + q * κ) / κ := by
    field_simp <;> ring
  rw [hden, div_eq_div_iff (div_pos (mul_pos hb hE) hκ).ne' hE.ne']
  ring

/-- (S2.6): with a bonus `b` per unit of the score and in the linear region of the effort rule
(true gain `c m δ b`, manipulation `b/κ`, equations S2.4 and S2.5), the cosmetic share of the
measured gain is `1/(1 + c m δ κ)`. -/
theorem cosmetic_share_bonus {c m δ κ b : ℝ} (hκ : 0 < κ) (hb : 0 < b) (hq : 0 ≤ c * m * δ) :
    (b / κ) / (c * m * δ * b + b / κ) = 1 / (1 + c * m * δ * κ) :=
  share_identity hκ hb hq

/-- (S2.6) for a mayor of average competence (`θ = 0`, so `m = 1`): `1/(1 + c δ κ)`. -/
theorem cosmetic_share_average_mayor {c δ κ b : ℝ} (hκ : 0 < κ) (hb : 0 < b) (hq : 0 ≤ c * δ) :
    (b / κ) / (c * 1 * δ * b + b / κ) = 1 / (1 + c * δ * κ) := by
  have hq' : 0 ≤ c * 1 * δ := by rw [mul_one]; exact hq
  have h := cosmetic_share_bonus (c := c) (m := 1) (δ := δ) hκ hb hq'
  rw [h]
  ring

/-- (S2.18): for an incentive `I` and effort `a`, the cosmetic share of the measured response is
`(I/κ) / (c m a + I/κ) = 1/(1 + κ c m a / I)`. -/
theorem cosmetic_share_identity {I κ x : ℝ} (hI : 0 < I) (hκ : 0 < κ) (hx : 0 ≤ x) :
    (I / κ) / (x + I / κ) = 1 / (1 + κ * x / I) := by
  have hI' : I ≠ 0 := hI.ne'
  have hκ' : κ ≠ 0 := hκ.ne'
  have h1 : 0 < x + I / κ := by
    have := div_pos hI hκ
    linarith
  have h2 : 0 < 1 + κ * x / I := by
    have := div_nonneg (mul_nonneg hκ.le hx) hI.le
    linarith
  rw [div_eq_div_iff h1.ne' h2.ne']
  field_simp <;> ring

/-- P3: the cosmetic share falls strictly as capacity rises, because real effort scales with
capacity while manipulation does not. -/
theorem cosmetic_share_falls_with_capacity {I κ m a c₁ c₂ : ℝ} (hI : 0 < I) (hκ : 0 < κ)
    (hm : 0 < m) (ha : 0 < a) (hc₁ : 0 ≤ c₁) (h12 : c₁ < c₂) :
    (I / κ) / (c₂ * m * a + I / κ) < (I / κ) / (c₁ * m * a + I / κ) := by
  have hIκ : 0 < I / κ := div_pos hI hκ
  apply aux_div_lt_div_left hIκ
  · have : 0 ≤ c₁ * m * a := mul_nonneg (mul_nonneg hc₁ hm.le) ha.le
    linarith
  · have h := mul_lt_mul_of_pos_right h12 (mul_pos hm ha)
    linarith

/-- In the linear region of the effort rule (`a = δ I`), (S2.18) reduces to (S2.6). -/
theorem cosmetic_share_linear_region {I κ c m δ : ℝ} (hI : 0 < I) (hκ : 0 < κ)
    (hq : 0 ≤ c * m * δ) :
    (I / κ) / (c * m * (δ * I) + I / κ) = 1 / (1 + c * m * δ * κ) := by
  have e : c * m * (δ * I) = c * m * δ * I := by ring
  rw [e]
  exact share_identity hκ hI hq

end LRG
