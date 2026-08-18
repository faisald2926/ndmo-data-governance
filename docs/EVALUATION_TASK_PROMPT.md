# Task prompt — measure Mizan's real accuracy with ALLaM running

> Paste everything below the line into the agent.

---

You're in the Mizan repo (NDMO data-governance platform). The README's **85.3% accuracy is the keyword baseline with the LLM switched off**. Nobody has ever measured the real ALLaM-7B path. Measure it, improve it, report it.

**Steps**

1. **Preflight.** Check Ollama is up and `iKhalid/ALLaM:7b` is pulled. Time one call, then multiply out — a full run is **10,558 calls (8,576 after cache)**; `--max-per-file 300` is **1,500 calls (1,087 after cache)**. If the full run looks like more than ~2 hours, use `--max-per-file 300` and say so in every number you report.

2. **Use `LLM_MODE=ollama`, not `auto`.** `auto` silently falls back to the keyword heuristic when Ollama is down, and you'd report a fake LLM score. Confirm afterwards that `decided_by` is mostly `allam` and `heuristic` is zero.

3. **Baseline, then measure.** Run `python pipeline.py --max-per-file N` then `python evaluate.py`, in offline mode and in ollama mode. Report both.

4. **Improve.** In this order: fix JSON parse failures in `llm.py::_parse_json` (every failure silently becomes `مقيّد` — check the rate first, it's probably the biggest win), then the system prompt in `prompts/ndmo_system_prompt.md`, then sweep `LLM_CONFIDENCE_THRESHOLD` (currently 0.55).

5. **Report** in `docs/EVALUATION_REPORT.md`: accuracy, the 4×4 confusion matrix, per-file accuracy, wall time, and hardware. Update the README with the ALLaM number *alongside* the offline baseline — don't replace it.

**Rules**

- **Don't add keywords to `_KEYWORDS` in `llm.py`.** Those lists came from this dataset; extending them to fix errors you observed is fitting the answer key, not improving the system.
- **Don't edit `ground_truth_labels.csv` or `quality_issues_log.csv`.** If a label looks wrong, note it, leave it.
- **Report over-declassification separately** — truth `سري`/`سري للغاية` predicted as `عام`. That's a governance failure; predicting `مقيّد` is just NDMO's safe default. Don't average them together.
- **If you tune anything, hold out 30% of the labels and only score it once at the end.** Otherwise your final number is meaningless.

**What to expect:** ~98% of the baseline's errors are one failure — no keyword matched, so it defaulted to `مقيّد`. That's exactly what the LLM should fix. If ALLaM doesn't clearly beat 85.3%, the problem is your prompt or your JSON parsing, not the ceiling.
