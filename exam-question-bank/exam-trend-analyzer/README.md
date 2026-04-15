# exam-trend-analyzer

A Claude skill that runs the full pipeline for analyzing exam-question-bank trends for a given app + subject, and produces a formatted Word report.

## Capabilities

1. **Fetch** — pull questions from Supabase by `app_id` + `category`
2. **Stats** — year distribution, answer distribution, stem length
3. **Keywords** — 2-4 gram frequency analysis
4. **AI topic tagging** — Claude Sonnet 4.6 labels every question against a per-subject topic list
5. **Deep analysis** — recent-vs-old cross comparison, hot keyword detection, topic stability (CV), priority ranking
6. **Word report** — 10-section formatted `.docx` with cover page, tables, and styled highlights

## Prerequisites

- Python 3.9+
- `anthropic` package: `pip install anthropic`
- Node.js + `docx` package: `npm install -g docx`
- `ANTHROPIC_API_KEY` environment variable (or `examproadmin/.env.local`)
- Supabase credentials (baked into `scripts/analyze_subject.py`)

## Usage

### One-shot (from scratch, for a supported subject)

```bash
APP=nurseexam
CAT=兒科護理學

python3 scripts/analyze_subject.py fetch    --app $APP --category $CAT
python3 scripts/analyze_subject.py stats    --input json_output/${CAT}.json
python3 scripts/analyze_subject.py keywords --input json_output/${CAT}.json --top 40
python3 scripts/analyze_subject.py tag      --input json_output/${CAT}.json --app $APP
python3 scripts/deep_analyze.py             --tagged json_output/${CAT}_tagged.json --subject $CAT --app $APP
node     scripts/build_report.js            json_output/${CAT}_analysis.json "$CAT" "$APP"
```

Final output: `兒科護理學_出題傾向分析報告.docx` (~25 KB, 10 chapters + appendix)

### Adding a new subject

1. Edit `configs/topic_configs.json`, add a key `"<app>:<category>"` with 10-15 topic strings
2. Run the pipeline

### Customizing keyword library (for non-nursing exams)

```bash
python3 scripts/deep_analyze.py \
    --tagged json_output/<cat>_tagged.json \
    --subject <cat> \
    --app <app> \
    --keywords-file my_custom_keywords.json
```

`my_custom_keywords.json` is a JSON array of strings.

## Directory Layout

```
exam-trend-analyzer/
├── SKILL.md                    # Skill manifest (Claude reads this)
├── README.md                   # This file
├── scripts/
│   ├── analyze_subject.py      # fetch / stats / keywords / tag / trends
│   ├── deep_analyze.py         # Produces <category>_analysis.json
│   └── build_report.js         # Consumes analysis.json → .docx
├── configs/
│   └── topic_configs.json      # Per-subject topic definitions
└── templates/                  # (reserved for future template variants)
```

## Tested Subjects

| App | Subject | Year range | Questions |
|---|---|---|---|
| nurseexam | 兒科護理學 | 100–114 | 1,542 |

## Notes

- The deep-analysis keyword library is nursing/clinical-heavy; for non-medical exams supply `--keywords-file`
- Topic tagging is cached per-category at `json_output/_topic_cache_<app>_<category>.json` — safe to resume and safe to reuse the same working directory across different subjects
- Stale cache entries whose IDs are not in the current input are discarded automatically
- `ANTHROPIC_API_KEY` is looked up from env → `./.env.local` → walking up to `examproadmin/.env.local` → skill-relative fallback
- Year parsing expects a `NNN年` pattern in `source` (Taiwan minguo year)
