# Validate lexical evidence before reranking

Base: upstream main 33b48812c95150348c52d2519159780252c92db2.
Branch: fix/relevance-before-rerank-gate. No dependency on judge, proxy or Jev.

The 128-pair Spanish study found 75 local shortlists with correct annotated evidence
rejected because reranking selected too few lexical hits. A permutation should not
erase evidence that the authorized candidate pool contains the query terms. Read the
lexical share from the hydrated, permission-scoped candidate pool before reordering;
continue reading the best rerank score from the returned shortlist. Preserve the 1/3
lexical share, 0.02 score floor, weak band and no-reranker behavior.

Prove reorder/limit invariance, zero-lexical and low-score refusals and hidden-label
isolation with real PostgreSQL. Validate 128 new published Spanish questions from
previously unused article families, plus independently labelled unanswerable controls.
Report ranking/admission metrics separately from generated-answer accuracy. Do not
retune the completed cohort or promise that removing a veto guarantees a supported answer.
