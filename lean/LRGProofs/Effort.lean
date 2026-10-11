import Mathlib
import LRGProofs.Basic

/-!
# Effort: equations (5) to (7) of the article, (S2.1) to (S2.3) of the Supplementary Material

The cost of effort rises steeply as effort approaches a ceiling `4δ` (equation 5). The mayor
chooses effort `a` to maximise `I·a - C(a)`, where `I` is the marginal expected incentive
(equation 4). This file proves that the effort rule of equation (7) is that choice, that it lies
below the ceiling, that it is close to `δ I` for small incentives (S2.3), that the cost is close
to `a²/(2δ)` for small efforts (S2.2), and that each additional unit of incentive buys less
effort.
-/

namespace LRG

/-- Cost of effort, equation (5) of the article: `C(a) = 16δ [-log(1 - a/(4δ)) - a/(4δ)]`. -/
noncomputable def cost (δ a : ℝ) : ℝ :=
  16 * δ * (-Real.log (1 - a / (4 * δ)) - a / (4 * δ))

/-- Marginal cost of effort, equation (6) of the article: `C'(a) = (a/δ) / (1 - a/(4δ))`. -/
noncomputable def marginalCost (δ a : ℝ) : ℝ :=
  (a / δ) / (1 - a / (4 * δ))

/-- The effort rule, equation (7) of the article: `a* = δ I / (1 + I/4)`. -/
noncomputable def effort (δ I : ℝ) : ℝ :=
  δ * I / (1 + I / 4)

/-! ## The cost function and its derivative -/

/-- Equation (6) is the derivative of equation (5), at every effort below the ceiling. -/
theorem hasDerivAt_cost {δ a : ℝ} (hδ : 0 < δ) (ha : a < 4 * δ) :
    HasDerivAt (fun x => cost δ x) (marginalCost δ a) a := by
  have hδ' : δ ≠ 0 := hδ.ne'
  have h4 : (0 : ℝ) < 4 * δ := by linarith
  have h4' : (4 : ℝ) * δ ≠ 0 := h4.ne'
  have h4a : 4 * δ - a ≠ 0 := (sub_pos.mpr ha).ne'
  have hpos : 0 < 1 - a / (4 * δ) := by
    have h := aux_div_lt_one h4 ha
    linarith
  have hpos' : 1 - a / (4 * δ) ≠ 0 := hpos.ne'
  have hx : HasDerivAt (fun x : ℝ => x / (4 * δ)) (1 / (4 * δ)) a :=
    (hasDerivAt_id a).div_const (4 * δ)
  have hlog : HasDerivAt (fun x : ℝ => Real.log (1 - x / (4 * δ)))
      (-(1 / (4 * δ)) / (1 - a / (4 * δ))) a :=
    (hx.const_sub 1).log hpos'
  have hsum : HasDerivAt (fun x : ℝ => 16 * δ * (-Real.log (1 - x / (4 * δ)) - x / (4 * δ)))
      (16 * δ * (-(-(1 / (4 * δ)) / (1 - a / (4 * δ))) - 1 / (4 * δ))) a :=
    ((hlog.neg).sub hx).const_mul (16 * δ)
  unfold cost marginalCost
  convert hsum using 1
  field_simp <;> ring

/-- Equation (6) in a simpler form: `C'(a) = 4a / (4δ - a)`. -/
theorem marginalCost_eq {δ a : ℝ} (hδ : 0 < δ) (ha : a < 4 * δ) :
    marginalCost δ a = 4 * a / (4 * δ - a) := by
  have hδ' : δ ≠ 0 := hδ.ne'
  have h4' : (4 : ℝ) * δ ≠ 0 := mul_ne_zero (by norm_num) hδ'
  have h4a : 4 * δ - a ≠ 0 := (sub_pos.mpr ha).ne'
  unfold marginalCost
  field_simp <;> ring

/-- The marginal cost rises with effort: the cost of effort is strictly convex below the
ceiling. -/
theorem marginalCost_lt {δ x y : ℝ} (hδ : 0 < δ) (hxy : x < y) (hy : y < 4 * δ) :
    marginalCost δ x < marginalCost δ y := by
  rw [marginalCost_eq hδ (lt_trans hxy hy), marginalCost_eq hδ hy]
  have hx' : 0 < 4 * δ - x := by linarith
  have hy' : 0 < 4 * δ - y := by linarith
  have hx'' : 4 * δ - x ≠ 0 := hx'.ne'
  have hy'' : 4 * δ - y ≠ 0 := hy'.ne'
  have key : 4 * y / (4 * δ - y) - 4 * x / (4 * δ - x)
      = 16 * δ * (y - x) / ((4 * δ - x) * (4 * δ - y)) := by
    field_simp <;> ring
  have hpos : 0 < 16 * δ * (y - x) / ((4 * δ - x) * (4 * δ - y)) :=
    div_pos (mul_pos (by linarith) (by linarith)) (mul_pos hx' hy')
  linarith

/-! ## The effort rule -/

/-- Equation (7) in two equivalent forms: `a* = 4δI/(4 + I)`. -/
theorem effort_eq {δ I : ℝ} (hI : 0 ≤ I) : effort δ I = 4 * δ * I / (4 + I) := by
  have h4 : (4 : ℝ) + I ≠ 0 := (by linarith : (0 : ℝ) < 4 + I).ne'
  have h4' : (1 : ℝ) + I / 4 ≠ 0 := (by linarith : (0 : ℝ) < 1 + I / 4).ne'
  unfold effort
  field_simp <;> ring

/-- The distance between effort and its ceiling: `4δ - a* = 16δ/(4 + I)`. -/
theorem ceiling_sub_effort {δ I : ℝ} (hI : 0 ≤ I) : 4 * δ - effort δ I = 16 * δ / (4 + I) := by
  rw [effort_eq hI]
  have h4 : (4 : ℝ) + I ≠ 0 := (by linarith : (0 : ℝ) < 4 + I).ne'
  field_simp <;> ring

theorem effort_nonneg {δ I : ℝ} (hδ : 0 ≤ δ) (hI : 0 ≤ I) : 0 ≤ effort δ I := by
  unfold effort
  exact div_nonneg (mul_nonneg hδ hI) (by linarith)

/-- Effort never reaches its ceiling `4δ`. -/
theorem effort_lt_ceiling {δ I : ℝ} (hδ : 0 < δ) (hI : 0 ≤ I) : effort δ I < 4 * δ := by
  have h := ceiling_sub_effort (δ := δ) hI
  have hpos : 0 < 16 * δ / (4 + I) := div_pos (by linarith) (by linarith)
  linarith

/-- At the effort rule the marginal cost equals the incentive. -/
theorem marginalCost_effort {δ I : ℝ} (hδ : 0 < δ) (hI : 0 ≤ I) :
    marginalCost δ (effort δ I) = I := by
  rw [marginalCost_eq hδ (effort_lt_ceiling hδ hI), ceiling_sub_effort hI, effort_eq hI]
  have h4 : (4 : ℝ) + I ≠ 0 := (by linarith : (0 : ℝ) < 4 + I).ne'
  have hδ' : δ ≠ 0 := hδ.ne'
  field_simp <;> ring

/-- Equation (S2.1): the first-order condition multiplied by `1 - a/(4δ)`,
`(a*/δ)(1 + I/4) = I`. -/
theorem effort_foc {δ I : ℝ} (hδ : 0 < δ) (hI : 0 ≤ I) :
    effort δ I / δ * (1 + I / 4) = I := by
  rw [effort_eq hI]
  have h4 : (4 : ℝ) + I ≠ 0 := (by linarith : (0 : ℝ) < 4 + I).ne'
  have hδ' : δ ≠ 0 := hδ.ne'
  field_simp <;> ring

/-- The effort rule is the only effort below the ceiling at which the marginal cost equals the
incentive. -/
theorem effort_unique {δ I a : ℝ} (hδ : 0 < δ) (hI : 0 ≤ I) (ha : a < 4 * δ)
    (h : marginalCost δ a = I) : a = effort δ I := by
  have hd : 4 * δ - a ≠ 0 := (sub_pos.mpr ha).ne'
  rw [marginalCost_eq hδ ha, div_eq_iff hd] at h
  rw [effort_eq hI, eq_div_iff (by linarith : (0 : ℝ) < 4 + I).ne']
  linear_combination h

/-- The effort rule is the mayor's best response: it maximises `I·a - C(a)` over all efforts
`0 ≤ a < 4δ`. This is the sense in which equation (7) follows from equating marginal cost and
the marginal expected incentive. -/
theorem effort_maximizes {δ I a : ℝ} (hδ : 0 < δ) (hI : 0 ≤ I) (ha0 : 0 ≤ a) (ha : a < 4 * δ) :
    I * a - cost δ a ≤ I * effort δ I - cost δ (effort δ I) := by
  have he4 : effort δ I < 4 * δ := effort_lt_ceiling hδ hI
  have hmc : marginalCost δ (effort δ I) = I := marginalCost_effort hδ hI
  have hg : ∀ x, x < 4 * δ → HasDerivAt
      (fun y => (I * effort δ I - cost δ (effort δ I)) - (I * y - cost δ y))
      (marginalCost δ x - I) x := by
    intro x hx
    have hid : HasDerivAt (fun y : ℝ => y) 1 x := hasDerivAt_id x
    have h2 := ((hid.const_mul I).sub (hasDerivAt_cost hδ hx)).const_sub
      (I * effort δ I - cost δ (effort δ I))
    convert h2 using 1
    ring
  rcases le_or_lt (effort δ I) a with hea | hae
  · -- above the effort rule, the payoff falls as effort rises
    have key : 0 ≤ (I * effort δ I - cost δ (effort δ I)) - (I * a - cost δ a) :=
      nonneg_of_deriv_nonneg_Ico
        (f := fun y => (I * effort δ I - cost δ (effort δ I)) - (I * y - cost δ y))
        (f' := fun y => marginalCost δ y - I) (c := effort δ I) (b := 4 * δ)
        (fun x hx => hg x hx.2)
        (fun x hx => by
          show 0 ≤ marginalCost δ x - I
          have h := marginalCost_lt hδ hx.1 hx.2
          rw [hmc] at h
          linarith)
        (by simp) a ⟨hea, ha⟩
    linarith
  · -- below the effort rule, the payoff rises with effort
    have key : 0 ≤ (I * effort δ I - cost δ (effort δ I)) - (I * a - cost δ a) :=
      nonneg_of_deriv_nonpos_Icc
        (f := fun y => (I * effort δ I - cost δ (effort δ I)) - (I * y - cost δ y))
        (f' := fun y => marginalCost δ y - I) (c := 0) (b := effort δ I)
        (fun x hx => hg x (lt_of_le_of_lt hx.2 he4))
        (fun x hx => by
          show marginalCost δ x - I ≤ 0
          have h := marginalCost_lt hδ hx.2 he4
          rw [hmc] at h
          linarith)
        (by simp) a ⟨ha0, hae.le⟩
    linarith

/-! ## Small incentives: (S2.3) -/

/-- `δI - a* = δI²/(4 + I)`. -/
theorem linear_sub_effort {δ I : ℝ} (hI : 0 ≤ I) : δ * I - effort δ I = δ * I ^ 2 / (4 + I) := by
  rw [effort_eq hI]
  have h4 : (4 : ℝ) + I ≠ 0 := (by linarith : (0 : ℝ) < 4 + I).ne'
  field_simp <;> ring

/-- `a* - δI(1 - I/4) = δI³/(4(4 + I))`. -/
theorem effort_sub_lower {δ I : ℝ} (hI : 0 ≤ I) :
    effort δ I - δ * I * (1 - I / 4) = δ * I ^ 3 / (4 * (4 + I)) := by
  rw [effort_eq hI]
  have h4 : (4 : ℝ) + I ≠ 0 := (by linarith : (0 : ℝ) < 4 + I).ne'
  field_simp <;> ring

/-- Upper half of (S2.3): effort never exceeds `δ I`. -/
theorem effort_le_linear {δ I : ℝ} (hδ : 0 ≤ δ) (hI : 0 ≤ I) : effort δ I ≤ δ * I := by
  have h := linear_sub_effort (δ := δ) hI
  have hpos : 0 ≤ δ * I ^ 2 / (4 + I) := div_nonneg (mul_nonneg hδ (sq_nonneg I)) (by linarith)
  linarith

/-- Lower half of (S2.3): effort is at least `δ I (1 - I/4)`. -/
theorem lower_le_effort {δ I : ℝ} (hδ : 0 ≤ δ) (hI : 0 ≤ I) : δ * I * (1 - I / 4) ≤ effort δ I := by
  have h := effort_sub_lower (δ := δ) hI
  have hpos : 0 ≤ δ * I ^ 3 / (4 * (4 + I)) :=
    div_nonneg (mul_nonneg hδ (pow_nonneg hI 3)) (by linarith)
  linarith

/-- (S2.3), `a* ≈ δ I`, with an explicit error: `|a* - δI| ≤ δI²/4`, so the relative error is at
most `I/4` and vanishes for small incentives. -/
theorem effort_approx {δ I : ℝ} (hδ : 0 ≤ δ) (hI : 0 ≤ I) :
    |effort δ I - δ * I| ≤ δ * I ^ 2 / 4 := by
  have h1 := effort_le_linear hδ hI
  have h2 := lower_le_effort hδ hI
  rw [abs_le]
  constructor
  · nlinarith
  · nlinarith [mul_nonneg hδ (sq_nonneg I)]

/-! ## Large incentives and diminishing returns -/

/-- As the incentive grows, effort approaches its ceiling `4δ`: it comes within any `ε > 0` of
the ceiling once `I ≥ 16δ/ε`. -/
theorem effort_approaches_ceiling {δ ε : ℝ} (hδ : 0 < δ) (hε : 0 < ε) :
    ∃ I₀ : ℝ, 0 ≤ I₀ ∧ ∀ I, I₀ ≤ I → 4 * δ - ε < effort δ I := by
  have hε' : ε ≠ 0 := hε.ne'
  have hN : 0 ≤ 16 * δ / ε := (div_pos (by linarith) hε).le
  refine ⟨16 * δ / ε, hN, ?_⟩
  intro I hI
  have hI0 : 0 ≤ I := le_trans hN hI
  have h4 : (0 : ℝ) < 4 + I := by linarith
  have h4' : (4 : ℝ) + I ≠ 0 := h4.ne'
  have hεI : 16 * δ ≤ ε * I := by
    have h1 : ε * (16 * δ / ε) = 16 * δ := by
      field_simp <;> ring
    have h2 : ε * (16 * δ / ε) ≤ ε * I := mul_le_mul_of_nonneg_left hI hε.le
    linarith
  have key : ε - 16 * δ / (4 + I) = (ε * (4 + I) - 16 * δ) / (4 + I) := by
    field_simp <;> ring
  have hpos : 0 < (ε * (4 + I) - 16 * δ) / (4 + I) := by
    apply div_pos _ h4
    nlinarith
  have hc := ceiling_sub_effort (δ := δ) hI0
  linarith

/-- The effort bought by an additional incentive `h`. -/
theorem effort_increment {δ I h : ℝ} (hI : 0 ≤ I) (hh : 0 ≤ h) :
    effort δ (I + h) - effort δ I = 16 * δ * h / ((4 + I) * (4 + I + h)) := by
  rw [effort_eq (by linarith : (0 : ℝ) ≤ I + h), effort_eq hI]
  have h1 : (4 : ℝ) + I ≠ 0 := (by linarith : (0 : ℝ) < 4 + I).ne'
  have h2 : (4 : ℝ) + (I + h) ≠ 0 := (by linarith : (0 : ℝ) < 4 + (I + h)).ne'
  have h3 : (4 : ℝ) + I + h ≠ 0 := (by linarith : (0 : ℝ) < 4 + I + h).ne'
  field_simp <;> ring

/-- Effort rises with the incentive. -/
theorem effort_strictMono {δ I J : ℝ} (hδ : 0 < δ) (hI : 0 ≤ I) (hIJ : I < J) :
    effort δ I < effort δ J := by
  have h := effort_increment (δ := δ) hI (by linarith : (0 : ℝ) ≤ J - I)
  rw [show I + (J - I) = J by ring] at h
  have hpos : 0 < 16 * δ * (J - I) / ((4 + I) * (4 + I + (J - I))) := by
    apply div_pos
    · exact mul_pos (by linarith) (by linarith)
    · exact mul_pos (by linarith) (by linarith)
  linarith

/-- Diminishing returns: the same additional incentive `h` buys less effort when the incentive
is already higher, so stacking incentives on the same mayor runs into diminishing returns. -/
theorem effort_diminishing {δ I J h : ℝ} (hδ : 0 < δ) (hI : 0 ≤ I) (hIJ : I < J) (hh : 0 < h) :
    effort δ (J + h) - effort δ J < effort δ (I + h) - effort δ I := by
  rw [effort_increment hI hh.le, effort_increment (by linarith : (0 : ℝ) ≤ J) hh.le]
  apply aux_div_lt_div_left
  · exact mul_pos (mul_pos (by norm_num) hδ) hh
  · exact mul_pos (by linarith) (by linarith)
  · nlinarith [mul_pos (sub_pos.mpr hIJ) (by linarith : (0 : ℝ) < 8 + I + J + h)]

/-! ## The cost of effort for small efforts: (S2.2) -/

/-- `-log(1 - x) - x ≥ x²/2` on `[0, 1)`. -/
theorem neg_log_one_sub_lower {x : ℝ} (hx0 : 0 ≤ x) (hx1 : x < 1) :
    x ^ 2 / 2 ≤ -Real.log (1 - x) - x := by
  have key : 0 ≤ -Real.log (1 - x) - x - x * x / 2 :=
    nonneg_of_deriv_nonneg_Ico
      (f := fun t => -Real.log (1 - t) - t - t * t / 2)
      (f' := fun t => t * t / (1 - t)) (c := 0) (b := 1)
      (fun t ht => by
        have h1 : 0 < 1 - t := by linarith [ht.2]
        have h1' : 1 - t ≠ 0 := h1.ne'
        have hid : HasDerivAt (fun y : ℝ => y) 1 t := hasDerivAt_id t
        have hl : HasDerivAt (fun y : ℝ => Real.log (1 - y)) (-1 / (1 - t)) t :=
          (hid.const_sub 1).log h1'
        have hall := ((hl.neg).sub hid).sub ((hid.mul hid).div_const 2)
        convert hall using 1
        field_simp <;> ring)
      (fun t ht => by
        show 0 ≤ t * t / (1 - t)
        exact div_nonneg (mul_self_nonneg t) (by linarith [ht.2]))
      (by simp) x ⟨hx0, hx1⟩
  have e : x ^ 2 / 2 = x * x / 2 := by ring
  rw [e]
  linarith

/-- `-log(1 - x) - x ≤ x²/(2(1 - x))` on `[0, 1)`. -/
theorem neg_log_one_sub_upper {x : ℝ} (hx0 : 0 ≤ x) (hx1 : x < 1) :
    -Real.log (1 - x) - x ≤ x ^ 2 / (2 * (1 - x)) := by
  have key : 0 ≤ x * x / (2 * (1 - x)) + Real.log (1 - x) + x :=
    nonneg_of_deriv_nonneg_Ico
      (f := fun t => t * t / (2 * (1 - t)) + Real.log (1 - t) + t)
      (f' := fun t => t * t / (2 * ((1 - t) * (1 - t)))) (c := 0) (b := 1)
      (fun t ht => by
        have h1 : 0 < 1 - t := by linarith [ht.2]
        have h1' : 1 - t ≠ 0 := h1.ne'
        have h2 : (2 : ℝ) * (1 - t) ≠ 0 := mul_ne_zero two_ne_zero h1'
        have hid : HasDerivAt (fun y : ℝ => y) 1 t := hasDerivAt_id t
        have hnum : HasDerivAt (fun y : ℝ => y * y) (1 * t + t * 1) t := hid.mul hid
        have hden : HasDerivAt (fun y : ℝ => 2 * (1 - y)) (2 * (-1)) t :=
          (hid.const_sub 1).const_mul 2
        have hq := hnum.div hden h2
        have hl : HasDerivAt (fun y : ℝ => Real.log (1 - y)) (-1 / (1 - t)) t :=
          (hid.const_sub 1).log h1'
        have hall := (hq.add hl).add hid
        convert hall using 1
        field_simp <;> ring)
      (fun t ht => by
        show 0 ≤ t * t / (2 * ((1 - t) * (1 - t)))
        exact div_nonneg (mul_self_nonneg t) (mul_nonneg (by norm_num) (mul_self_nonneg (1 - t))))
      (by simp) x ⟨hx0, hx1⟩
  have e : x ^ 2 / (2 * (1 - x)) = x * x / (2 * (1 - x)) := by ring
  rw [e]
  linarith

/-- Lower half of (S2.2): the cost of effort is at least `a²/(2δ)`. -/
theorem cost_ge_quadratic {δ a : ℝ} (hδ : 0 < δ) (ha0 : 0 ≤ a) (ha : a < 4 * δ) :
    a ^ 2 / (2 * δ) ≤ cost δ a := by
  have h4 : (0 : ℝ) < 4 * δ := by linarith
  have hδ' : δ ≠ 0 := hδ.ne'
  have hx0 : 0 ≤ a / (4 * δ) := div_nonneg ha0 h4.le
  have hx1 : a / (4 * δ) < 1 := aux_div_lt_one h4 ha
  have h := neg_log_one_sub_lower hx0 hx1
  have e : a ^ 2 / (2 * δ) = 16 * δ * ((a / (4 * δ)) ^ 2 / 2) := by
    field_simp <;> ring
  unfold cost
  rw [e]
  exact mul_le_mul_of_nonneg_left h (by linarith)

/-- Upper half of (S2.2): the cost of effort is at most `(a²/(2δ)) / (1 - a/(4δ))`. With the
lower half, `C(a) / (a²/(2δ))` lies between `1` and `1/(1 - a/(4δ))`, which tends to one as
effort tends to zero: `C(a) ≈ a²/(2δ)`. -/
theorem cost_le {δ a : ℝ} (hδ : 0 < δ) (ha0 : 0 ≤ a) (ha : a < 4 * δ) :
    cost δ a ≤ a ^ 2 / (2 * δ) / (1 - a / (4 * δ)) := by
  have h4 : (0 : ℝ) < 4 * δ := by linarith
  have hδ' : δ ≠ 0 := hδ.ne'
  have h4a : 4 * δ - a ≠ 0 := (sub_pos.mpr ha).ne'
  have hx0 : 0 ≤ a / (4 * δ) := div_nonneg ha0 h4.le
  have hx1 : a / (4 * δ) < 1 := aux_div_lt_one h4 ha
  have hx1' : 1 - a / (4 * δ) ≠ 0 := (by linarith : (0 : ℝ) < 1 - a / (4 * δ)).ne'
  have h := neg_log_one_sub_upper hx0 hx1
  have e : a ^ 2 / (2 * δ) / (1 - a / (4 * δ))
      = 16 * δ * ((a / (4 * δ)) ^ 2 / (2 * (1 - a / (4 * δ)))) := by
    field_simp <;> ring
  unfold cost
  rw [e]
  exact mul_le_mul_of_nonneg_left h (by linarith)

end LRG
