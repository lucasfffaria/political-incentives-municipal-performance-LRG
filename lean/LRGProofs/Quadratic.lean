import Mathlib

/-!
# Quadratic costs: equation (9) of the article, (S2.11) and the textbook contract of (S2.3)

Several choices in the model weigh a linear gain against a quadratic cost: manipulation of the
reported number (equation 9), clientelist mobilisation (S2.11, in `Clientelism.lean`) and the
textbook linear contract recalled after (S2.3). They share one fact: `B x - κ x²/2`, with `κ > 0`,
is maximised at `x = B/κ` and nowhere else.
-/

namespace LRG

/-- Completing the square: the payoff at `B/κ` exceeds the payoff at `x` by `κ (x - B/κ)²/2`. -/
theorem quadratic_gap {B κ : ℝ} (hκ : 0 < κ) (x : ℝ) :
    (B * (B / κ) - κ * (B / κ) ^ 2 / 2) - (B * x - κ * x ^ 2 / 2)
      = κ * ((x - B / κ) * (x - B / κ)) / 2 := by
  have hκ' : κ ≠ 0 := hκ.ne'
  field_simp <;> ring

/-- `B/κ` maximises `B x - κ x²/2`. -/
theorem quadratic_argmax {B κ : ℝ} (hκ : 0 < κ) (x : ℝ) :
    B * x - κ * x ^ 2 / 2 ≤ B * (B / κ) - κ * (B / κ) ^ 2 / 2 := by
  have h := quadratic_gap (B := B) hκ x
  have hpos : 0 ≤ κ * ((x - B / κ) * (x - B / κ)) / 2 :=
    div_nonneg (mul_nonneg hκ.le (mul_self_nonneg _)) (by norm_num)
  linarith

/-- `B/κ` is the only maximiser of `B x - κ x²/2`. -/
theorem quadratic_argmax_unique {B κ x : ℝ} (hκ : 0 < κ)
    (h : B * x - κ * x ^ 2 / 2 = B * (B / κ) - κ * (B / κ) ^ 2 / 2) : x = B / κ := by
  have hg := quadratic_gap (B := B) hκ x
  have h0 : κ * ((x - B / κ) * (x - B / κ)) = 0 := by linarith
  rcases mul_eq_zero.mp h0 with h1 | h1
  · exact absurd h1 hκ.ne'
  · have h2 := mul_self_eq_zero.mp h1
    linarith

/-- Equation (9) of the article: with a quadratic cost of manipulation `κ g²/2`, a marginal
incentive `I` inflates the reported number by `g* = I/κ`. -/
theorem manipulation_optimal {I κ : ℝ} (hκ : 0 < κ) (g : ℝ) :
    I * g - κ * g ^ 2 / 2 ≤ I * (I / κ) - κ * (I / κ) ^ 2 / 2 :=
  quadratic_argmax hκ g

/-- The textbook linear contract recalled after (S2.3): a reward `b` per unit of an indicator that
effort raises with productivity `α`, at cost `k e²/2`, is best answered with effort `bα/k`, and
the indicator then rises by `α²b/k`. -/
theorem linear_contract {b α k : ℝ} (hk : 0 < k) (e : ℝ) :
    (b * α * e - k * e ^ 2 / 2 ≤ b * α * (b * α / k) - k * (b * α / k) ^ 2 / 2) ∧
      α * (b * α / k) = α ^ 2 * b / k := by
  constructor
  · exact quadratic_argmax hk e
  · ring

end LRG
