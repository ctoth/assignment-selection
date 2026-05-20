# Papers

Reference literature for `assignment-selection`. Each entry is a full paper
directory; the PDF source and PNG page-renders are kept on disk only (see the
repo `.gitignore`) — the notes, abstracts, claims, and metadata are tracked.

The merge operators this library implements (`SIGMA`, `MAX`, `GMAX`) come from
the IC-merging family; Konieczny & Pino-Pérez 2002 is the direct theoretical
basis.

## Belief merging — direct basis

## [Merging Information Under Constraints](Konieczny_2002_MergingInformationUnderConstraints/notes.md)  (belief-merging, integrity-constraints, distance-based-semantics)
Defines the IC merging framework with postulates IC0-IC8 and the three operator
families this library mirrors: Sigma (majority), Max (quasi-merging), GMax
(arbitration). The representation theorems linking axiomatic operators to
distance-based pre-orders are the correctness criteria for `solve`.

## [Merging Dung's Argumentation Systems](Coste-Marquis_2007_MergingDungsArgumentationSystems/notes.md)  (argumentation-merging, distance-based-merging)
Lifts the IC-merging distance operators (sum/max/leximax) to argumentation
frameworks. Reference for how the same aggregation family generalises beyond
propositional bases.

## Belief revision — foundations

## [On the Logic of Theory Change (AGM)](Alchourron_1985_TheoryChange/notes.md)  (belief-revision, agm, contraction)
The AGM postulates for rational contraction and revision; partial meet
constructions and their representation theorems. The postulate-driven
correctness style assignment-selection's contracts follow.

## [Two Modellings for Theory Change](Grove_1988_TwoModellingsTheoryChange/notes.md)  (belief-revision, sphere-semantics)
Systems of spheres and sentence orderings as model-theoretic accounts of AGM
change — the cleanest picture of distance/closeness semantics over finite worlds.

## [Knowledge in Flux — Epistemic Entrenchment](Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/notes.md)  (belief-revision, epistemic-entrenchment)
Epistemic entrenchment as a total preorder governing retraction priority, with a
representation theorem against AGM contraction.

## [New Operators for Theory Change](Hansson_1989_NewOperatorsTheoryChange/notes.md)  (belief-revision, belief-bases)
Extends theory change to non-closed belief bases and set-valued inputs —
relevant to treating source assignments as bases rather than closed theories.

## [Admissible and Restrained Revision](Booth_2006_AdmissibleRestrainedRevision/notes.md)  (belief-revision, iterated-revision)
Characterises the admissible subclass of iterated revision operators; restrained
revision as the most conservative member.

## [Ordinal Conditional Functions](Spohn_1988_OrdinalConditionalFunctionsDynamic/notes.md)  (belief-revision, ordinal-conditional-functions)
Kappa-functions as ordinal epistemic states supporting iterated, reversible
change — the metric substrate underneath distance-based merging.
