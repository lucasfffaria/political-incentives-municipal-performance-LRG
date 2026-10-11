import Lake
open Lake DSL

package «LRGProofs» where
  -- every variable must be declared: no automatic implicit arguments
  leanOptions := #[⟨`autoImplicit, false⟩]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.15.0"

@[default_target]
lean_lib «LRGProofs» where
  -- the library is the folder LRGProofs/ and the root file LRGProofs.lean
