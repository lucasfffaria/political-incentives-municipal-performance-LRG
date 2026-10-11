import Mathlib

/-!
# Party funds: (S2.20) and proposition P5

Under the proposed rule, as codified in Section S1.2 of the Supplementary Material, the share of
the Fundo Partidário of a party is proportional to the positive points of its mayors weighted by
the population they govern, `Σ_{i ∈ S} n_i max(P_i, 0)`, where `S` is the set of municipalities
governed by the party's mayors. This file proves the arithmetic of the rule that the proof of P5
uses: a party can raise its score by recruiting a mayor whose points are already positive, or by
improving the points of its own mayors. Which route is cheaper is an economic argument about
costs and observability, made in the text, not a theorem.
-/

namespace LRG

open Finset

/-- (S2.20): the score of a party, `Σ_{i ∈ S} n_i max(P_i, 0)`. -/
noncomputable def partyScore {ι : Type*} (S : Finset ι) (n P : ι → ℝ) : ℝ :=
  ∑ i ∈ S, n i * max (P i) 0

/-- Recruiting the mayor of a municipality `j` not yet governed by the party raises its score by
`n_j max(P_j, 0)`, without any change in the services of any municipality. -/
theorem partyScore_recruit {ι : Type*} [DecidableEq ι] (S : Finset ι) (n P : ι → ℝ) {j : ι}
    (hj : j ∉ S) :
    partyScore (insert j S) n P = partyScore S n P + n j * max (P j) 0 := by
  unfold partyScore
  rw [sum_insert hj]
  ring

/-- A recruited mayor with positive points and a positive population strictly raises the
score. -/
theorem partyScore_recruit_gain {ι : Type*} [DecidableEq ι] (S : Finset ι) (n P : ι → ℝ) {j : ι}
    (hj : j ∉ S) (hn : 0 < n j) (hP : 0 < P j) :
    partyScore S n P < partyScore (insert j S) n P := by
  rw [partyScore_recruit S n P hj]
  have hmax : max (P j) 0 = P j := max_eq_left hP.le
  rw [hmax]
  have := mul_pos hn hP
  linarith

/-- Improving the points of the party's own mayors raises its score. -/
theorem partyScore_mono {ι : Type*} (S : Finset ι) (n P P' : ι → ℝ) (hn : ∀ i ∈ S, 0 ≤ n i)
    (hP : ∀ i ∈ S, P i ≤ P' i) : partyScore S n P ≤ partyScore S n P' := by
  unfold partyScore
  apply sum_le_sum
  intro i hi
  apply mul_le_mul_of_nonneg_left _ (hn i hi)
  exact max_le_max (hP i hi) le_rfl

end LRG
