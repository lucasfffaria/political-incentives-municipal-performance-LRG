import LRGProofs.Effort
import LRGProofs.Quadratic
import LRGProofs.Cosmetic
import LRGProofs.ContractTheory
import LRGProofs.Sanctions
import LRGProofs.Information
import LRGProofs.Money
import LRGProofs.Parties
import LRGProofs.Clientelism
import LRGProofs.Implementation

/-!
# Which axioms the proofs use

Building this file prints, for the main theorems, the axioms on which their proofs rest. Only
Lean's three standard axioms should appear: `propext`, `Classical.choice` and `Quot.sound`. The
axiom `sorryAx` would reveal a proof left unfinished.
-/

#print axioms LRG.hasDerivAt_cost
#print axioms LRG.effort_maximizes
#print axioms LRG.effort_unique
#print axioms LRG.effort_approx
#print axioms LRG.effort_diminishing
#print axioms LRG.cost_ge_quadratic
#print axioms LRG.cost_le
#print axioms LRG.quadratic_argmax_unique
#print axioms LRG.cosmetic_share_bonus
#print axioms LRG.cosmetic_share_falls_with_capacity
#print axioms LRG.hmWeight_falls_with_noise
#print axioms LRG.hmWeight_can_rise_with_substitution
#print axioms LRG.bakerRate_lt_one_iff
#print axioms LRG.bakerRate_can_exceed_one
#print axioms LRG.hasDerivAt_sanctionProb_place
#print axioms LRG.hasDerivAt_sanctionProb_mayor
#print axioms LRG.misclassification_strictMono
#print axioms LRG.fail_at_least_one_tendsto
#print axioms LRG.sanction_term_far
#print axioms LRG.corr_function_le
#print axioms LRG.cov_change_lagged_noise
#print axioms LRG.concave_transfer
#print axioms LRG.partyScore_recruit_gain
#print axioms LRG.hasDerivAt_mobilisation_tied
#print axioms LRG.hasDerivAt_implQuality
#print axioms LRG.implQuality_ban_lowers
