# Spanish reranking results

The user authorized up to 100,000 Jev calls or another $5 on 2026-10-01. The evaluation
limits BOTH calls and spend. It made 5,173 calls, all successful, using 2,712,168 reported
input tokens and $0.113911056 at the pinned jev-1.13.0 rate of $0.042/million input tokens.
This is usage accounting, not a provider invoice. The key was supplied only in memory for
the authorized run. No Jev product client or distributed quota system was introduced.

| Fixed panel: 648 queries | nDCG@8 | MRR@8 | Hit@1 | Recall@8 |
| --- | ---: | ---: | ---: | ---: |
| BM25 within each human-judged pool | 0.69971 | 0.69459 | 0.52778 | 0.85188 |
| Cached mMiniLM / CPU | 0.78905 | 0.84965 | 0.76698 | 0.85188 |
| BGE-reranker-v2-m3 / GPU | 0.81761 | 0.88362 | 0.81327 | 0.85188 |
| Jev-1.13.0 | 0.82976 | 0.89514 | 0.82716 | 0.85188 |

Jev minus mMiniLM nDCG@8: +0.04071168, paired family-cluster bootstrap 95% interval
[+0.02866289, +0.05348700]. Jev minus BGE: +0.01215167, interval
[+0.00246723, +0.02218987]. BGE's mean gain and lower bound do not meet the preselected
meaningful-gain threshold of 0.02. Its MRR/Hit@1 intervals cross zero. The result does not
justify replacing BGE. Recall@8 stays identical because reranking permutes the same
selected candidates. All 648 queries completed for each model, with zero fallback queries.

Local whole-query rerank median/p95: mMiniLM 1.488/3.201 seconds; BGE 0.443/0.727 seconds.
Jev's individual-pair median: 0.255 seconds with four concurrent calls. Different units and
concurrency policies prevent a full-query cloud/local latency comparison. No generation,
ingestion or WAN upload latency is included.

## Published human ground truth

No new human annotation is required for this benchmark. The MIRACL Spanish dev parquet
contains all 648 queries with their human-judged positive and negative passage texts. Every
ID, label and coverage set was checked against the already pinned original qrels. The
full Spanish Wikipedia corpus is unnecessary for this conditional reranking experiment.

Parquet revision: ad2acf33f265b8fba92e5096c9d2cf569a82b067; 2,654,970 bytes. Public Spanish
evaluation data now total 72,150,538 bytes, excluding Hub bookkeeping. SQAC dev/test,
ALIA BOJA/ParlaMint CQA, legal triplets and original MIRACL topics/qrels remain available.
BGE weights/tokenizers were additionally downloaded at
953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e; weights alone are 2,271,071,852 bytes.
Raw datasets and weights remain ignored under .local-data. Exact file sizes, revisions and
SHA-256 hashes are in spanish-data-manifest.json and spanish-rerank-results.json.

Frozen panel SHA-256: 73a22b895cec9c9b5a7c906232831145f39a59c50ea118e2353946060e92cfa0.
All development queries were held out for this run; no prompt/model/threshold tuning used
their outcomes. Query text is capped at 512 characters and title plus passage at 1,000 for
all models. Candidates are shuffled by query/passage-ID hash, ranked with BM25 k1=1.2,
b=0.75 over each judged pool, then limited to at most eight. No gold passage is injected.
TEI uses batches of at most four with a 2,048-token budget and explicit truncation.
Scores are ordered only within each provider; ties preserve candidate order. The Jev
Spanish instruction judges direct answering evidence, rather than topical word overlap.
Bootstrap: 601 connected positive-article-family groups, 2,000 resamples, seed 20261001.

mMiniLM is cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 at
1427fd652930e4ba29e8149678df786c240d8825, CPU TEI 1.8.3. BGE is the model named by the
reranker implementation constant; development Compose defaults to mMiniLM. BGE ran on
RTX 5070 Ti with float16, using image digest
sha256:bd8e5b1954146f7fe8590b64b959bc194433c6c38c036592a84d736841ca9400, reporting TEI
1.9.4. This model/image/precision difference is not a controlled CPU/GPU speedup experiment.
The unchanged Jev ledger was reused for BGE, adding zero paid calls.

## Reproduce

Download the converted Spanish dev parquet with the installed hf CLI:

```powershell
hf download miracl/miracl es/dev/0000.parquet --repo-type dataset --revision ad2acf33f265b8fba92e5096c9d2cf569a82b067 --local-dir .local-data/spanish/miracl-human-dev
python scripts/local-first/spanish_rerank.py prepare --source .local-data/spanish/miracl-human-dev/es/dev/0000.parquet --qrels .local-data/spanish/miracl-es/miracl-v1.0-es/qrels/qrels.miracl-v1.0-es-dev.tsv --panel .local-evidence/followup/spanish/frozen-panel.json
python scripts/local-first/spanish_rerank.py local --panel .local-evidence/followup/spanish/frozen-panel.json --endpoint http://127.0.0.1:18094 --output .local-evidence/followup/spanish/local-bge-gpu.json
python scripts/local-first/spanish_rerank.py summarize --panel .local-evidence/followup/spanish/frozen-panel.json --local .local-evidence/followup/spanish/local-bge-gpu.json --jev .local-evidence/followup/spanish/jev-ledger.jsonl --output .local-evidence/followup/spanish/bge-comparison.json
```

Paid mode uses the SAME durable ledger and an in-memory TYPESAFE_API_KEY or stdin. It
reserves the documented maximum 64k input-token charge before dispatch, retains unknown
outcomes at that maximum, validates model/schema/usage before settling, never retries paid
failures, and refuses a panel-hash mismatch. Do not reset the session budget by creating a
fresh ledger: later experiments must include this run's spend/calls. A completed ledger
skips previously assessed pairs on resume. No additional calls are needed for this panel.

## Limits

These are conditional rankings of human-judged Spanish Wikipedia pools, not whole-corpus
retrieval, generated-answer correctness, scanned tables or universal Spanish superiority.
Labels refer to full original passages; shared truncation can remove relevant evidence.
Model training overlap with MIRACL is unknown. Grouping uses shared positive articles,
not a guarantee against every topical dependency. Confidence is conditional on this panel.

SQAC supplies expert general QA, while ALIA legal/admin answers are synthetic and its
downloaded triplet evaluation lacks negative fields. Those datasets are domain fixtures,
not evidence of legal superiority. Published human judgments replaced the proposed manual
annotation gate. Dataset cards retain their annotation/document licenses and attribution.

Sources: [MIRACL](https://huggingface.co/datasets/miracl/miracl),
[BGE](https://huggingface.co/BAAI/bge-reranker-v2-m3),
[Jev documentation](https://docs.typesafe.ai/introduction).
