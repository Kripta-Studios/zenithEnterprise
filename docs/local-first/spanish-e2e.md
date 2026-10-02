# Spanish generated answers with mandatory citations

This experiment evaluates the actual Zenith upload, ingestion, retrieval, generated-answer,
citation-binding and audit path. It does not enable Jev in the product. The comparison is
against the existing BGE GPU reranker. Results and a publication decision are pending the
completed paired run and independent local entailment checks.

## Frozen design

Published SQAC human answer spans supply the reference labels. The corpus contains all 634
test contexts and 16 development contexts, 650 total. Sixteen development questions choose
between exactly two Spanish Jev criteria; 128 test questions are selected independently by
fixed SHA-256 ordering with seed 20261002, one question per selected context. Development
and test context hashes are disjoint. There are no injected gold candidates or exclusions
based on model performance.

Both arms retrieve 32 real hybrid candidates and send the eight reranked passages to the
same local Llama 3.1 8B Instruct Q4_K_M generator. They use the existing product prompt, HTTP query route,
permissions, citation binding and query audit writes. The common experimental client
profile uses two items and 1,024 estimated tokens per batch; production defaults remain
unchanged. The original BGE model, not a deliberately weakened local baseline, is compared.

Llama 3.1 runs on the existing local Ollama installation with thinking disabled,
temperature zero, seed 20261002, context 8192 and output limit 256. Its manifest digest is
46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e. Model and request options
are identical in both arms; identical full prompts can reuse their original completion.

The primary metric requires the generated answer to contain a human reference answer,
a bound citation to the actual source filename and character range containing that
annotated span, a marker for every answer sentence, and independent NLI entailment >=0.8
for every sentence. The independent judge is the local multilingual
MoritzLaurer/mDeBERTa-v3-base-mnli-xnli model at revision
8adb042d524ecd5c26d3e3ba0e3fbcf7e2d0864c, CPU float32. Long cited premises use overlapping
token windows; inputs are not silently truncated. Neither provider identity nor Jev
scores are provided to this judge. A positive and an unsupported Spanish sanity example
must pass before grading. Span-only accuracy, answer F1, citation coverage, retrieval
nDCG@8/recall and abstentions are reported separately.

The preregistered meaningful primary gain is at least 0.02 with a strictly positive 95%
CI lower bound. A clearly larger gain requires at least 0.05 and a lower bound >=0.02.
Intervals use paired article-cluster bootstrap, 2,000 resamples and seed 20261002. The old
MIRACL nDCG@8 gain threshold of 0.02 is a separate ranking criterion, not the same metric.
Test results cannot change the selected criteria, generator, selection or thresholds.

## Real execution boundaries and ingestion finding

Limited available RAM requires sequential model stages. The first stage records actual
embedding vectors and real authenticated retrieval candidates against the live disposable
database. After actual BGE/Jev scoring, each HTTP query reruns retrieval against that same
database and verifies the full candidate identity and order, then uses the recorded actual
scores and calls the local generator. The result exercises the functional path, including
database audit assertions, but is not a simultaneous online deployment latency measurement.

Two failed attempts are retained. First, the experimental two-item embedding service
rejected a four-item client request; the benchmark profile was then applied consistently
to the existing pipeline. Second, the entire corpus in one file reached the PostgreSQL
statement timeout while inserting chunk embeddings. No database timeout was increased.
Before any scoring, the identical corpus was partitioned into 14 files of about 64,000
characters, split only between published contexts. Joining those texts restores the exact
original corpus checksum; all questions and references are unchanged. The bounded actual
run uploaded 844,617 text bytes and persisted 939 chunks in 257.365 seconds to ready.
The reconstructed corpus is 844,643 bytes; the 26-byte difference is the two-newline
separator between the 14 files, whose boundaries are restored for the corpus checksum.
The single-document bulk embedding INSERT is an observed ingestion bottleneck requiring
separate product work; this benchmark changes only its input file layout.

Before generating any test answer, the original cached `qwen3:4b` tag failed neutral
Spanish readiness probes. Its GGUF metadata identifies Qwen3-4B-Thinking-2507, which
cannot use the planned non-thinking mode. `think:false`, `/no_think`, and an explicit
closed-thinking raw template still exhausted the 256-token budget on reasoning. Those
failed probes are retained. The waiting first bounded pipeline was stopped before any
test generation. Llama 3.1 Instruct was already cached and passed a neutral Spanish
arithmetic readiness probe in six output tokens. The pipeline is restarted with this
model for both arms; corpus, questions, retrieval policy, Jev criterion, output budget
and evaluation thresholds are unchanged. The initial and effective protocols are both
retained. No generator selection used answer quality from the test questions.

On a technical restart, existing pair scores can be rebound to new disposable database
UUIDs only after matching every question, filename, character range and full passage
text. Any unscored passage stops replay. A fresh model run must retain the original
development criterion freeze and the complete cumulative budget ancestry. This cache
does not inject candidates or change the actual repeated retrieval in the query route.
In this run replay refused 259 previously unscored candidates after UUID tie ordering
changed the pool. Both providers were therefore scored again against the final actual
pool, with the original development criterion retained. A separate retry fixes transient
Docker Desktop snapshot rename failures caused by host readers; permanent failures still
propagate. The final 14-file upload-to-ready measurement is 234.100 seconds, with the same
939 persisted chunks. These two timings are individual local observations, not an SLA.

The authorized caps remain 100,000 calls and $5, including the earlier 5,173 calls and
$0.113911056. Every paid request is durably reserved before dispatch; unknown outcomes
are not retried. Paid inputs must exactly match question strings and source spans in the
frozen public SQAC fixture. No private customer text, reference labels or new product
external-provider integration is sent to Jev. Cost is reported input-token accounting at
$0.042 per million for pinned jev-1.13.0, not a billing invoice.

## Reproduction

The benchmark lives in `backend/eval/spanish_e2e.py`,
`backend/eval/tests/test_spanish_e2e_pipeline.py`, and
`backend/eval/spanish_e2e_nli.py`. `scripts/local-first/spanish_e2e.py` runs actual local
or Jev scoring, retaining cumulative ledgers and the development-only criterion freeze.
Use the pinned SQAC raw files from the existing Spanish dataset manifest. Preparation
and model weights are ignored local artifacts; no dataset, completion, credential or
model binary is committed.

The effective generator is the already cached multilingual
[Llama 3.1 Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct).
The rejected Qwen tag's metadata and neutral probes agree with the
[Thinking-2507 model's documented thinking-only mode](https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507).

Run the opt-in pipeline with `scripts/local-first/docker_checks.py`,
`--test-path eval/tests/test_spanish_e2e_pipeline.py` and `--spanish-e2e-panel` pointing
at the prepared public fixture. Keep its disposable database alive while the model
stages run. Score its `candidates.json` with both modes, supplying the prior ledger and
`--public-fixture` for Jev. Write `models-ready.json` only after scoring and local
generator readiness. The pipeline then completes 128 paired real HTTP queries.
Run `python -m eval.spanish_e2e_nli --results generated-results.json --model` pointing
at the pinned local NLI snapshot `--output independently-graded.json` to produce the
complete aggregate and bootstrap intervals. Full backend and measurement dependencies
are needed on the host; the lean pipeline container does not load Torch or Transformers.

## Interpretation limits

Published extractive QA labels remove the need to construct new human answer references.
They do not provide human judgments of every generated claim. Exact reference matching
can miss valid paraphrases; automatic multilingual NLI can make mistakes. This is a
public Spanish QA experiment, not proof of correctness on private contracts or legal
documents. Neither a ranking improvement nor a generated-answer gain resolves external
egress or multiworker quota concerns. Product adoption remains a separate decision.
