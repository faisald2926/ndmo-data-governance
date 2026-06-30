# NDMO Data Governance · حوكمة البيانات

Automated data **classification**, **quality monitoring**, and **lineage** aligned with Saudi **NDMO** standards — with a bilingual **Arabic-first** web UI and **role-based access control**. The classifier runs locally on **ALLaM-7B** via Ollama, so no data leaves the host.

🌐 [English](#english) · [العربية](#بالعربية)

---

<a name="english"></a>
## English

### Overview
A containerised data-governance platform: **FastAPI + PostgreSQL + Ollama (ALLaM-7B) + a custom bilingual web UI**. It classifies data into the four NDMO sensitivity levels, monitors the six NDMO quality dimensions, traces lineage from source to report, and enforces role-based access — the four pain points the challenge names: random classification, manual compliance, lost lineage, and poor quality.

### Features
- **Classification** — 3-layer hybrid: deterministic rules/regex (Saudi national ID via Luhn, IBAN via mod-97, phone, VAT) → **ALLaM-7B** (local) for free text → a policy engine (default-to-Restricted, highest-level-on-aggregation). Evidence + rationale on every decision.
- **Data quality** — the 6 NDMO dimensions (Completeness, Uniqueness, Timeliness, Validity, Accuracy, Consistency) with thresholds and per-row findings.
- **Lineage** — OpenLineage-style `source → transform → report`; a report inherits the highest level of its inputs.
- **RBAC** — Admin and Viewer roles, token-based auth, append-only audit log.
- **Bilingual UI** — Arabic-first (RTL) with a one-click switch to English, served at `:8000`.

### Quickstart (Docker)
```bash
cp .env.example .env            # Windows PowerShell: Copy-Item .env.example .env
docker compose up -d --build    # postgres + app (UI + API at :8000); Postgres auto-loads seed data
```
Open http://localhost:8000, then run the pipeline and score it:
```bash
docker compose exec app python pipeline.py --max-per-file 300
docker compose exec app python evaluate.py
```
> Ollama runs natively on the host by default (`OLLAMA_BASE_URL=http://host.docker.internal:11434`). To run Ollama in a container instead: `docker compose --profile with-ollama up -d --build`.

### Access & roles (RBAC)
| Role | Demo login | Can do |
|------|-----------|--------|
| **Admin** | `admin / admin123` | manage users, edit a record's severity, run the pipeline, seed data, full read access |
| **Viewer** | `viewer / viewer123` | read-only: records and their urgency, quality findings, lineage, evaluation |

Change `JWT_SECRET` and `ADMIN_PASSWORD` in `.env` before any real use.

### The model
ALLaM-7B (Saudi sovereign model) via Ollama, tag `iKhalid/ALLaM:7b` (~4.5 GB Q4 — fits an 8 GB GPU). No GPU? set `LLM_MODE=offline` (rules + keyword fallback). Smaller GPU? `LLM_MODEL=qwen2.5:3b-instruct`.

### Evaluation
The dataset ships answer keys, so scoring is automatic. `GET /evaluate` (or the dashboard's Evaluation tab) returns classification accuracy + confusion matrix and quality precision/recall. Offline baseline: **accuracy 0.817**, **quality precision 0.974 / recall 0.971**. The production ALLaM-7B number comes from `evaluate` after a real run.

### Project structure
```
app/    FastAPI — classification/  quality/  lineage/  ingestion/  auth.py  main.py  static/ (web UI)
data/   synthetic datasets + answer keys        db/postgres_seed.sql
prompts/ndmo_system_prompt.md   docker-compose.yml   Makefile   .env.example
```

### Notes
All data is **synthetic**. The local model means no data leaves the host (PDPL-friendly). No fine-tuning yet — an AraBERT / QLoRA track is a documented next step.

---

<a name="بالعربية"></a>
<div dir="rtl">

## بالعربية

### نظرة عامة
منصّة حوكمة بيانات حاوية (Docker): **FastAPI + PostgreSQL + Ollama (ALLaM-7B) + واجهة ويب مخصّصة ثنائية اللغة**. تُصنّف البيانات إلى مستويات NDMO الأربعة، وتراقب أبعاد الجودة الستة، وتتبّع الأثر من المصدر إلى التقرير، وتطبّق صلاحيات الوصول حسب الدور — وهي معالجة مباشرة للتحديات الأربعة: عشوائية التصنيف، والامتثال اليدوي، وفقدان الأثر، وضعف الجودة.

### المزايا
- **التصنيف** — هجين من ثلاث طبقات: قواعد وأنماط حتمية (الهوية الوطنية عبر Luhn، الآيبان عبر mod-97، الجوال، الرقم الضريبي) ← **ALLaM-7B** محلي للنص الحر ← طبقة سياسات (الافتراضي «مقيّد»، والمستوى الأعلى عند التجميع). مع دليل وتبرير لكل قرار.
- **جودة البيانات** — أبعاد NDMO الستة (الاكتمال، التفرّد، الحداثة، الصحة، الدقة، الاتساق) مع عتبات وتنبيهات على مستوى الصف.
- **تتبّع الأثر** — أحداث بنمط OpenLineage: المصدر ← المعالجة ← التقرير؛ ويرث التقرير أعلى مستوى من مصادره.
- **الصلاحيات (RBAC)** — دورا «مدير» و«مشاهد»، مصادقة برمز، وسجل تدقيق غير قابل للتعديل.
- **واجهة ثنائية اللغة** — عربية أولاً (من اليمين لليسار) مع تبديل فوري للإنجليزية، على المنفذ 8000.

### التشغيل السريع (Docker)
```bash
cp .env.example .env
docker compose up -d --build
```
افتح http://localhost:8000 ثم شغّل المعالجة والتقييم:
```bash
docker compose exec app python pipeline.py --max-per-file 300
docker compose exec app python evaluate.py
```
> يعمل Ollama محليًا على الجهاز افتراضيًا. ولتشغيله داخل حاوية: `docker compose --profile with-ollama up -d --build`.

### الصلاحيات والأدوار
| الدور | الدخول (تجريبي) | الصلاحيات |
|------|----------------|-----------|
| **مدير** | `admin / admin123` | إدارة المستخدمين، تعديل مستوى السجل، تشغيل المعالجة، تحميل البيانات، واطلاع كامل |
| **مشاهد** | `viewer / viewer123` | اطلاع فقط: السجلات ومستوى حساسيتها، الجودة، الأثر، التقييم |

غيّر `JWT_SECRET` و`ADMIN_PASSWORD` في `.env` قبل أي استخدام فعلي.

### النموذج
ALLaM-7B (نموذج سعودي سيادي) عبر Ollama بالوسم `iKhalid/ALLaM:7b` (~4.5 جيجابايت Q4 — يناسب بطاقة 8 جيجابايت). بدون بطاقة رسومية: `LLM_MODE=offline`. لبطاقة أصغر: `LLM_MODEL=qwen2.5:3b-instruct`.

### التقييم
تتضمّن البيانات مفاتيح إجابات، لذا التقييم آلي. يعطي `/evaluate` (أو تبويب التقييم في الواجهة) دقة التصنيف ومصفوفة الالتباس، ودقة/استرجاع الجودة. الأساس دون النموذج: **الدقة 0.817**، **جودة البيانات: دقة 0.974 / استرجاع 0.971**. ويأتي رقم ALLaM-7B الفعلي بعد تشغيل حقيقي.

### هيكل المشروع
```
app/    FastAPI — classification/  quality/  lineage/  ingestion/  auth.py  main.py  static/ (واجهة الويب)
data/   البيانات الاصطناعية + مفاتيح الإجابات     db/postgres_seed.sql
prompts/ndmo_system_prompt.md   docker-compose.yml   Makefile   .env.example
```

### ملاحظات
جميع البيانات **اصطناعية**. تشغيل النموذج محليًا يعني عدم خروج البيانات من الجهاز (متوافق مع PDPL). لا يوجد ضبط دقيق بعد — مسار AraBERT / QLoRA خطوة مستقبلية موثّقة.

</div>
