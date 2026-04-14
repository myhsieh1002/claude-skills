---
name: exam-trend-analyzer
description: "Use this skill to analyze exam question-bank trends for a specific app and subject. Downloads questions from Supabase, performs basic statistics, keyword frequency analysis, Claude-assisted topic tagging, cross-year trend comparison (recent vs historical), hot-keyword detection, topic stability analysis, and produces a Word report. Trigger keywords: 出題傾向分析, 題庫趨勢, 考題分析, 分科分析, 題庫分析, exam trend analysis, subject trend, question bank analysis, exam tendency, 考點分布, 年度趨勢."
---

# Exam Trend Analyzer Skill

## Overview

Given an **app_id** and **subject (category)** in a Supabase-backed exam question bank, produce a full trend analysis including:

1. Raw fetch from Supabase (`questions` table)
2. Basic statistics (year / answer / length distribution)
3. Keyword frequency (2–4 gram)
4. AI topic tagging (Claude API) against a per-subject topic list
5. Cross-year comparison (recent N years vs prior)
6. Hot keyword detection (近期爆紅考點)
7. Topic stability analysis (variation coefficient)
8. Prioritized study recommendations
9. Word report output (`.docx`)

Designed for Taiwan national exam style question banks (nurseexam, pharmexam, medexam, etc.) where each row has `question / options / answer / category / source`.

---

## When to Use

Trigger when user says things like:
- 「幫我分析 X 科的出題傾向」
- 「跑一次 [分科] 的題庫趨勢分析」
- 「產出一份 [分科] 的考點分布報告」
- 「分析近 5 年 X 科考什麼」

**Required inputs from user:**
- `app_id` (e.g. `nurseexam`, `medexam`)
- `category` / subject name (e.g. `兒科護理學`, `內外科護理學`)

**Optional:**
- year range (default: all years in DB)
- output directory (default: current working dir)

---

## Workflow

### Step 0. Verify topic config exists

Check `configs/topic_configs.json` for a key matching `{app_id}:{category}`.

If missing, **propose** a topic list (10–15 clinical subtopics) based on the subject name, confirm with the user, then add to `topic_configs.json` before proceeding.

### Step 1. Fetch questions

```bash
python3 scripts/analyze_subject.py fetch --app <APP> --category <CATEGORY>
```
Output: `json_output/<category>.json`

### Step 2. Basic stats

```bash
python3 scripts/analyze_subject.py stats --input json_output/<category>.json
```
Output: `json_output/<category>.stats.json` + console summary

### Step 3. Keyword frequency

```bash
python3 scripts/analyze_subject.py keywords --input json_output/<category>.json --top 40
```

### Step 4. AI topic tagging

```bash
python3 scripts/analyze_subject.py tag --input json_output/<category>.json --app <APP>
```
Output: `json_output/<category>_tagged.json` (each question has `topic` field)

Uses Claude Sonnet 4.6 in batches of 25. Cached in `json_output/_topic_cache.json`.

Requires `ANTHROPIC_API_KEY` environment variable OR a `.env.local` file in an adjacent `examproadmin` folder.

### Step 5. Deep analysis (trends + hotspots + stability)

```bash
python3 scripts/deep_analyze.py --tagged json_output/<category>_tagged.json --subject <CATEGORY> --app <APP>
```
Produces `json_output/<category>_analysis.json` with:
- `topic_distribution`
- `recent_vs_old` (近 5 年 vs 前 10 年)
- `hot_keywords` (近 3 年爆紅)
- `stability` (變異係數)
- `priority_recommendations`
- `subtopic_keywords`

### Step 6. Generate Word report

```bash
node scripts/build_report.js json_output/<category>_analysis.json "<CATEGORY>" "<APP>"
```
Output: `<CATEGORY>_出題傾向分析報告.docx` in current directory

Requires `docx` npm package globally installed: `npm install -g docx`

---

## Default Subject Settings

See `configs/topic_configs.json`. Currently covers:

| app_id | category |
|---|---|
| nurseexam | 兒科護理學, 內外科護理學, 產科護理學, 基礎醫學, 精神科護理學, 社區衛生護理學 |

Add new subjects by appending a key `{app_id}:{category}` with a list of 10–15 topic strings.

---

## Supabase Credentials

The analyzer uses the ExamPro Supabase project by default. To use a different project, edit `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `scripts/analyze_subject.py` (or read from env).

---

## Output Artifacts

After a full run, the working directory contains:

```
json_output/
├── <category>.json              # raw questions
├── <category>.stats.json        # basic stats
├── <category>_tagged.json       # with AI topic labels
├── <category>_analysis.json     # deep analysis summary (consumed by reporter)
└── _topic_cache.json            # AI tagging cache (persistent)
<category>_出題傾向分析報告.docx  # final Word report
```

---

## Quality Checks

Before declaring done:
- [ ] Total fetched questions > 0
- [ ] All questions have non-null `topic` after step 4
- [ ] Analysis JSON has all 6 sections
- [ ] Word report validates as ZIP + document.xml parses
- [ ] Report章節序號從 1 到 10 完整

---

## Extension Points

- **New language/exam**: swap STOPWORDS and DISEASE_KEYWORDS in `deep_analyze.py`
- **Different topic granularity**: edit `topic_configs.json`
- **Different output format**: add a `build_report_html.js` or similar alongside the Word script
- **Different recency threshold**: pass `--recent-years 3` to deep_analyze.py
