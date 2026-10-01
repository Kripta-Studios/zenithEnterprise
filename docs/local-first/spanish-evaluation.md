# Spanish reranking evidence preparation

Public downloads completed on 2026-10-01: 69,495,568 bytes, excluding Hub bookkeeping.
Exact repository revisions, filenames, byte counts and SHA-256 hashes are in
`spanish-data-manifest.json`. Files remain under `.local-data/spanish/`, outside Git.
Provider calls: zero. No Jev key has been written to disk, passed to a command, or used.

| Source | Downloaded scope | Ground truth and limits |
| --- | --- | --- |
| PlanTL-GOB-ES/SQAC | dev and test JSON, source card | Expert annotated general Spanish QA; 1,864 dev and 1,910 test questions. Context-level retrieval labels can be derived from the supplied answer spans. |
| SINAI/ALIA-es-legal-administrative-cqa | BOJA and ParlaMint-ES-AN parquet, card | Synthetic questions/answers from Spanish legal and administrative texts. The card reports 17,668 examples; they are not human relevance judgments. |
| SINAI/ALIA-es-legal-administrative-triplets | evaluation JSONL and card | Actually parsed: 11,059 rows and 10,125 passage IDs. The downloaded evaluation rows have no negative fields. Training hard-negative claims do not establish evaluation negatives. |
| miracl/miracl | Spanish topics/qrels and card | Human relevance judgments; the full Wikipedia corpus was not downloaded. This is not a runnable complete MIRACL benchmark yet. |

SQAC and the two ALIA cards declare CC BY-SA 4.0; MIRACL's card declares Apache 2.0
for its dataset annotations. Source documents have their own provenance and terms.
These are local research fixtures, not new shipped application dependencies or licensed
customer data. Keep the cards and attribution when sharing derived evaluation material.

Re-download with the installed `hf` CLI using each pinned revision, for example:

```powershell
hf download PlanTL-GOB-ES/SQAC dev.json test.json README.md --repo-type dataset --revision f9928e8819596a601b8887cc5f8598b15d589a82 --local-dir .local-data/spanish/sqac
hf download SINAI/ALIA-es-legal-administrative-cqa boja.parquet parlamint_es_an.parquet README.md --repo-type dataset --revision eeb7de37cdccebed7b29fa9f6a86cd8747145e43 --local-dir .local-data/spanish/alia-cqa
hf download SINAI/ALIA-es-legal-administrative-triplets ALIA-es-legal-administrative-triplets-eval.jsonl README.md --repo-type dataset --revision 0a3753db69cd99923f953b8a3fde3d42fb6e8ca8 --local-dir .local-data/spanish/alia-triplets
hf download miracl/miracl --repo-type dataset --revision 5be20db9509754dadad47689368639fcec739c00 --include 'README.md' 'miracl-v1.0-es/*' --local-dir .local-data/spanish/miracl-es
python scripts/local-first/prepare_spanish_data.py
```

The future experiment tests whether Jev improves outcomes; it must accept a negative result.
It has not been run and the key does not authorize paid calls. Keep these experiments off
the two accepted extraction branches and out of the immediate upstream product proposal.

Before a provider run, freeze a manifest of queries, document families, chunk boundaries,
retrieval candidates in original order, all text/token budgets, model/image revisions and
label permissions. Exclude identical contexts across splits and group legal documents by
source_id so passages from one regulation cannot appear in both tuning and test sets.
Use held-out questions once: no prompt or threshold selection from their outcomes.

Compare unchanged RRF, existing local TEI, the provider-neutral TEI adapter, and eventually
Jev on the exact same candidate panel. A shortlist of eight is the first fixed CPU-depth
comparison; a separate depth study must state its changed workload. Do not compare unrelated
raw confidence or score scales across providers. Preserve candidate IDs and tie rules.

For legal questions, independently annotate pooled lexical/dense hard negatives and multiple
valid passages with blinded human review. Detect false negatives, near duplicates, obsolete
versions, cross-references and passages that merely share a term. ALIA's synthetic answers
cannot certify legal correctness. SQAC context positives alone also leave alternative
correct answers unjudged; document that limitation rather than counting all others as wrong.

Report paired nDCG@8, MRR and Recall@8 with document-family bootstrap confidence intervals;
abstentions, partial assessments and fallback coverage; warmed stage latency p50/p95 and
full request latency; bytes/tokens, actual billable cost and failure rate. Keep one fixed
local generator for a separate cited-answer experiment with independent citation and
support judgments. A better rerank metric alone does not establish better generated answers.

Freeze the minimum meaningful improvement and latency/cost ceiling before running. Report
harmful slices and uncertainty even if the overall average improves. Tables, scanned pages,
contracts and tax regulations still need representative human-reviewed examples; the present
download does not establish coverage of every intended Zenith workload.

Primary sources: the pinned dataset cards linked in the manifest and
https://docs.typesafe.ai/introduction (typed judgments, not evidence of Spanish superiority).
