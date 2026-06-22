# NDMO Data Governance System

Automated **data classification**, **data-quality monitoring**, and **lineage tracing** aligned with Saudi NDMO standards — built for the Data Governance Challenge. Python · FastAPI · PostgreSQL · Ollama (ALLaM-7B) · Streamlit, all in Docker.

> Phase 2 build: full backend (classification + quality + lineage) + an easy dashboard. The classifier is **prompt-based on a local model — no fine-tuning yet**.

## What it does

1. **Classification** — a 3-layer hybrid labels every record `سري للغاية / سري / مقيّد / عام` with evidence + rationale:
   - **L1 rules/regex** — Saudi national ID (Luhn), IBAN (mod-97), phone, VAT, plus an Arabic/English column lexicon → catches structured PII deterministically.
   - **L2 local LLM** — ALLaM-7B via Ollama, driven by the NDMO system prompt, JSON output, for free-text/ambiguous content.
   - **L3 policy** — enforces NDMO's hard rules: *highest level on aggregation* and *default to Restricted* when unsure, attaches the control recommendation, flags `needs_review`.
2. **Quality** — scores data against the 6 NDMO dimensions (Completeness, Uniqueness, Timeliness, Validity, Accuracy, Consistency) with per-row findings.
3. **Lineage** — OpenLineage-style events (source → transform → report) showing how a Restricted report inherits its level.

## Architecture

```
Streamlit dashboard ─┐
                     ▼
              FastAPI app ──► PostgreSQL   (records, classifications, quality, lineage, audit)
                │
                ├─ classification (rules → ALLaM → policy)
                ├─ quality (6 dimensions)
                └─ lineage (aggregation rule)
                     │
                     ▼
              Ollama (ALLaM-7B, GPU)
```

## Quickstart (GPU)

Requires Docker, an NVIDIA GPU, and the NVIDIA Container Toolkit.

```bash
cp .env.example .env
make up                 # build + start postgres, ollama, app, dashboard
make pull-model         # pull ALLaM-7B into Ollama (one time, a few minutes)
make seed-data          # load the datasets into Postgres tables (raw_* + keys)
make pipeline           # ingest → classify → quality → lineage (300 rows/file)
make eval               # accuracy + quality precision/recall vs answer keys
```

### Hardware (tuned for 8 GB, e.g. RTX 3070)

ALLaM Q4 is ~4.5 GB, so it fits an 8 GB GPU with room for context. The defaults
keep VRAM low and speed high: model **keep-alive**, **num_ctx=2048**,
**num_predict=256**, response **caching**, and **concurrent** classification
(`LLM_CONCURRENCY`). Smaller machines, with little quality loss:
- **<6 GB VRAM** → `LLM_MODEL=qwen2.5:3b-instruct`
- **No GPU** → `LLM_MODE=offline` (rules + keyword fallback)
- **Windows GPU** is often smoothest with **native Ollama** + Docker for the rest:
  set `OLLAMA_BASE_URL=http://host.docker.internal:11434` and start everything
  except the `ollama` service.

### Use the official weights you downloaded (optional)

To run the exact HUMAIN safetensors instead of `ollama pull`:
`bash scripts/convert_to_gguf.sh <safetensors-dir>` → `ollama create allam-7b -f ollama/Modelfile` → set `LLM_MODEL=allam-7b`.

### Data in PostgreSQL

`make seed-data` (or `POST /data/seed`) loads all six datasets plus the three
answer-key files into Postgres as `raw_vendors`, `raw_invoices`,
`raw_employees`, `raw_citizen_requests`, `raw_documents`, `raw_open_datasets`,
`ground_truth_labels`, `quality_issues_log`, and `data_dictionary`.

- Dashboard → http://localhost:8501
- API docs → http://localhost:8000/docs

### No GPU? Run offline

The system degrades gracefully: set `LLM_MODE=offline` (or just run the target) and the LLM layer uses a transparent keyword classifier so everything still works.

```bash
make offline-demo       # full pipeline, rules + keyword fallback, no Ollama needed
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | status + active model / mode |
| POST | `/classify` | classify one text or record (live) |
| POST | `/pipeline/run` | ingest → classify → quality → lineage over the datasets |
| GET | `/stats` | level distribution, needs-review, quality by dimension |
| GET | `/records` | classified records (filter by level / source) |
| GET | `/quality/findings` | quality defects (filter by dimension) |
| GET | `/lineage` | lineage graph + events |
| GET | `/evaluate` | accuracy + confusion matrix + quality precision/recall |

Example:
```bash
curl -X POST localhost:8000/classify -H 'Content-Type: application/json' \
  -d '{"text":"أعاني من حالة صحية وأطلب إعفاءً، هويتي 1043215789"}'
```

## How it maps to NDMO

- **4 levels + 4 impact categories** encoded in `app/classification/ndmo.py`.
- **Default-to-Restricted** and **highest-on-aggregation** enforced in `policy.py` and `lineage/tracer.py`.
- **Classify-by-source** rule: open-data content → Public.
- **6 quality dimensions** with thresholds in `app/quality/engine.py`.
- **Evidence + rationale** on every decision (the policy demands evidence-based classification).
- The **system prompt** is a first-class, editable artifact: `prompts/ndmo_system_prompt.md` (runtime copy in `app/classification/system_prompt.py`).

## Evaluation

The mounted `data/` ships answer keys, so you can score the system:
- **Classification** — predictions vs `ground_truth_labels.csv` → accuracy + confusion matrix.
- **Quality** — findings vs `quality_issues_log.csv` → precision/recall per dimension.

Run `make eval` or open the dashboard's **التقييم** tab.

## Project structure

```
app/
  classification/  rules.py · system_prompt.py · llm.py · policy.py · classifier.py · ndmo.py
  quality/engine.py        lineage/tracer.py        ingestion/loader.py
  pipeline.py  evaluate.py  main.py  models.py  db.py  config.py
dashboard/app.py           prompts/ndmo_system_prompt.md
data/                      (the synthetic datasets + answer keys)
docker-compose.yml  Makefile  .env.example
```

## Configuration (`.env`)

| Var | Default | Notes |
|---|---|---|
| `LLM_MODEL` | `iKhalid/ALLaM:7b` | Ollama model tag |
| `LLM_MODE` | `auto` | `auto` \| `ollama` \| `offline` |
| `OLLAMA_BASE_URL` | host.docker.internal:11434 | point at your Ollama |
| `POSTGRES_*` | ndmo / ndmo_pass / ndmo | database creds |

## Notes

- **No fine-tuning** in this phase — prompt + few-shot only. A fine-tuning track (AraBERT / QLoRA) is a documented future step.
- All `data/` is **synthetic**; real data is suitable only for the Public tier.
- The local LLM means **no data leaves the host** — a PDPL-friendly property.
