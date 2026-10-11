import Mathlib

/-!
# Elementary helpers

Small facts about real division, and two consequences of the mean value theorem, written once and
used by the other files. They are proved from first principles so that the rest of the
development depends on as few named Mathlib lemmas as possible.
-/

namespace LRG

/-- `a / b < 1` when `0 < b` and `a < b`. -/
theorem aux_div_lt_one {a b : ℝ} (hb : 0 < b) (h : a < b) : a / b < 1 := by
  have h1 : a / b - b / b = (a - b) / b := by ring
  have h2 : (a - b) / b < 0 := div_neg_of_neg_of_pos (by linarith) hb
  have h3 : b / b = 1 := div_self hb.ne'
  linarith

/-- For `0 < b`, `a / b < 1` exactly when `a < b`. -/
theorem aux_div_lt_one_iff {a b : ℝ} (hb : 0 < b) : a / b < 1 ↔ a < b := by
  constructor
  · intro h
    by_contra hab
    push_neg at hab
    have h1 : a / b - b / b = (a - b) / b := by ring
    have h2 : 0 ≤ (a - b) / b := div_nonneg (by linarith) hb.le
    have h3 : b / b = 1 := div_self hb.ne'
    linarith
  · exact aux_div_lt_one hb

/-- Dividing both sides of an inequality by the same positive number. -/
theorem aux_div_le_div_right {a b c : ℝ} (hab : a ≤ b) (hc : 0 < c) : a / c ≤ b / c := by
  have h1 : b / c - a / c = (b - a) / c := by ring
  have h2 : 0 ≤ (b - a) / c := div_nonneg (by linarith) hc.le
  linarith

/-- A positive number divided by a larger positive denominator is smaller. -/
theorem aux_div_lt_div_left {x A B : ℝ} (hx : 0 < x) (hA : 0 < A) (hAB : A < B) :
    x / B < x / A := by
  have hB : 0 < B := lt_trans hA hAB
  have hA' : A ≠ 0 := hA.ne'
  have hB' : B ≠ 0 := hB.ne'
  have h1 : x / A - x / B = x * (B - A) / (A * B) := by
    field_simp <;> ring
  have h2 : 0 < x * (B - A) / (A * B) := div_pos (mul_pos hx (by linarith)) (mul_pos hA hB)
  linarith

/-- A function that is zero at `c` and has a non-negative derivative on `(c, b)` is
non-negative on `[c, b)` (mean value theorem). -/
theorem nonneg_of_deriv_nonneg_Ico {f f' : ℝ → ℝ} {c b : ℝ}
    (hd : ∀ x ∈ Set.Ico c b, HasDerivAt f (f' x) x)
    (hf' : ∀ x ∈ Set.Ioo c b, 0 ≤ f' x) (hc : f c = 0) :
    ∀ x ∈ Set.Ico c b, 0 ≤ f x := by
  have hmono : MonotoneOn f (Set.Ico c b) := by
    apply monotoneOn_of_deriv_nonneg (convex_Ico c b)
    · intro x hx
      exact (hd x hx).continuousAt.continuousWithinAt
    · intro x hx
      rw [interior_Ico] at hx
      exact (hd x ⟨hx.1.le, hx.2⟩).differentiableAt.differentiableWithinAt
    · intro x hx
      rw [interior_Ico] at hx
      rw [(hd x ⟨hx.1.le, hx.2⟩).deriv]
      exact hf' x hx
  intro x hx
  have hcmem : c ∈ Set.Ico c b := ⟨le_refl c, lt_of_le_of_lt hx.1 hx.2⟩
  have h := hmono hcmem hx hx.1
  rw [hc] at h
  exact h

/-- A function that is zero at `b` and has a non-positive derivative on `(c, b)` is
non-negative on `[c, b]` (mean value theorem). -/
theorem nonneg_of_deriv_nonpos_Icc {f f' : ℝ → ℝ} {c b : ℝ}
    (hd : ∀ x ∈ Set.Icc c b, HasDerivAt f (f' x) x)
    (hf' : ∀ x ∈ Set.Ioo c b, f' x ≤ 0) (hb : f b = 0) :
    ∀ x ∈ Set.Icc c b, 0 ≤ f x := by
  have hanti : AntitoneOn f (Set.Icc c b) := by
    apply antitoneOn_of_deriv_nonpos (convex_Icc c b)
    · intro x hx
      exact (hd x hx).continuousAt.continuousWithinAt
    · intro x hx
      rw [interior_Icc] at hx
      exact (hd x ⟨hx.1.le, hx.2.le⟩).differentiableAt.differentiableWithinAt
    · intro x hx
      rw [interior_Icc] at hx
      rw [(hd x ⟨hx.1.le, hx.2.le⟩).deriv]
      exact hf' x hx
  intro x hx
  have hbmem : b ∈ Set.Icc c b := ⟨le_trans hx.1 hx.2, le_refl b⟩
  have h := hanti hx hbmem hx.2
  rw [hb] at h
  exact h

end LRG
