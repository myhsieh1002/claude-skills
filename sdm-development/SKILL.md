---
name: sdm-development
description: "Use this skill for any task related to Shared Decision Making (SDM) / 醫病共享決策. This includes: reviewing/auditing existing SDM decision aids (PDAs), enhancing or rewriting SDMs based on review findings, developing new SDMs from scratch, filling out SDM evaluation scoring forms (醫策會評分表), and conducting literature searches for SDM evidence. Trigger on keywords: SDM, 共享決策, 決策輔助, PDA, patient decision aid, 評分表, 包皮, 馬龍, MACE, or any clinical scenario where the user wants to create a tool to help patients choose between treatment options."
---

# SDM (Shared Decision Making) Development & Review Skill

## Overview

This skill covers the full lifecycle of SDM decision aid (PDA) development for a Taiwanese hospital context (中山醫學大學附設醫院). It supports three work modes and one auxiliary task:

1. **Review Mode** — Audit an existing SDM against the 醫策會 evaluation framework
2. **Enhance Mode** — Rewrite/strengthen an SDM based on review findings, output as .docx
3. **Develop Mode** — Create a new SDM from scratch (research → plan → confirm → write)
4. **Scoring Mode** (auxiliary) — Fill out the 醫策會 PDA evaluation xlsx form

---

## Work Mode Detection

| User says | Mode |
|---|---|
| "幫我審查這份SDM" / "review this PDA" | Review |
| "幫我改良/強化這份SDM" / "依照分析改良" | Enhance |
| "幫我製作一個新的SDM" / "我想開發SDM" | Develop |
| "幫我填寫評分表" | Scoring |

If the user provides both an SDM file and a scoring form xlsx, default to **Enhance + Scoring** (review → enhance → score).

---

## 1. Review Mode

### Input
- An existing SDM document (.docx, .pdf, or pasted text)

### Analysis Framework (mirrors 醫策會 evaluation criteria)
Analyze the SDM across these dimensions, providing specific findings and improvement suggestions for each:

#### A. 醫療專業 (Medical Professional, 60 points)

**Content Presentation (30 pts)**
1. **Target population clarity (3 pts)** — Are inclusion/exclusion criteria clearly defined? Are they clinically actionable?
2. **SDM necessity (3 pts)** — Is this a preference-sensitive decision? Is the rationale for SDM clearly stated?
3. **Natural disease course (3 pts)** — Is the untreated/no-intervention trajectory described with quantified data?
4. **Decision options (3 pts)** — Are all reasonable options listed? Are they mutually exclusive or combinable? Is "no treatment" included if appropriate?
5. **Process information (4 pts)** — Are pre/during/post treatment procedures described for each option?
6. **Evidence-based comparison (4 pts)** — Are outcomes data from best available evidence presented numerically? Are ARR/NNT provided when applicable?
7. **Fair comparison (4 pts)** — Are options compared in equal detail, equal formatting, symmetric tone? Watch for: asymmetric side effect presentation, misleading symbols (✅/❌), unbalanced language
8. **Values clarification (6 pts)** — Does it help patients identify what matters most? Are dimensions balanced (pro/con for each option)? Cover physical, psychological, social, practical domains

**Patient comprehension (5 pts)**
9. **Readability (3 pts)** — Plain language, medical terms explained, clear tables/figures
10. **Knowledge assessment (2 pts)** — True knowledge test questions (not value questions!), with answer key, covering key decision-relevant facts

**Development process (20 pts)**
11. **Needs assessment (5 pts)** — Evidence of user needs evaluation (focus groups, interviews, literature)
12. **Pilot testing (5 pts)** — Evidence of usability/acceptability testing with target users
13. **Evidence search strategy (10 pts)** — Literature search methods, inclusion/exclusion criteria, evidence quality ratings, update policy

**Overall (5 pts)**
14. **Overall quality** — Holistic assessment of structure, logic flow, clinical utility

#### B. 民眾教育 (Patient Education, 40 points)

Items 1-12 (basic, 38 pts) + Items 13-14 (bonus, 2 pts) — see scoring form for details.

#### C. 整體回饋 (Overall Feedback)
- Length: too long / too short / appropriate
- Information amount: too much / too little / appropriate
- Fairness: balanced or biased toward ___
- Other suggestions

### Output Format
Present findings conversationally in Chinese, organized by dimension. Highlight:
- **Critical issues** (structural problems like wrong question types in Step 3)
- **Major improvements needed** (missing evidence levels, asymmetric comparison)
- **Minor suggestions** (wording, additional dimensions)

### Common Pitfalls to Flag
- Step 3 (知識確認) contains value/attitude questions instead of knowledge test questions
- Side effects listed asymmetrically between options (e.g., listing Drug A side effects for Option 1 but Drug B side effects for Option 2, when both options use Drug B)
- Missing ARR/NNT when absolute risk data is available
- Inconsistent terminology (e.g., "住院" vs "門診" for radiation therapy)
- ✅/❌ symbols oversimplifying nuanced outcomes
- Evidence level not stated
- Options presented as mutually exclusive when they can be combined

---

## 2. Enhance Mode

### Input
- Original SDM document + review findings (from Review Mode or user-provided analysis)

### Process
1. Read the docx skill at `/mnt/skills/public/docx/SKILL.md`
2. Create enhanced SDM as .docx using docx-js (npm `docx` package)
3. Validate with `python scripts/office/validate.py`
4. Copy to `/mnt/user-data/outputs/` and present

### SDM Document Structure Template

Every SDM should contain these sections in order:

```
1. Title (醫病共享決策輔助工具)
2. 前言 (Foreword) — Why this decision matters, what this tool does
3. 適用對象 (Eligibility) — Clear inclusion criteria, table format preferred
4. 疾病背景 (Disease Background) — Use patient-oriented Q&A format:
   - "What is [condition]?"
   - "Why does [factor] matter?"
   - "What happens without treatment?"
5. 證據摘要 (Evidence Summary) — Table with:
   - Study names, journal, year
   - Evidence level (explicitly stated: Level I = RCT/meta-analysis, etc.)
   - Key outcome numbers
   - ARR and NNT when calculable
6. 醫療選項比較表 (Options Comparison Table) — Unified format, symmetric detail
7. 初步意向 (Initial Preference) — Checkbox selection
8. 步驟一：回顧比較表 (Review comparison)
9. 步驟二：價值澄清/評分系統 (Values clarification / Scoring system)
10. 步驟三：知識確認 (Knowledge test) — MUST be objective true/false questions with answer key
11. 步驟四：決策確認 (Decision confirmation) — Include "undecided" with specific reason options
12. 簽名欄 (Signature) — Physician/SDM coach, Patient, Family/Guardian
13. 品質評估問卷 (Quality evaluation) — Standard 8 Likert + 2 open questions
14. 參考文獻 (References)
```

### Design Principles

**Values Clarification (步驟二)**
- Minimum 6 dimensions
- Directional balance: equal number of items favoring each option
- Use 1-5 Likert scale with endpoint descriptors
- Cover: physical, psychological, social, economic, practical domains

**Scoring System (when requested)**
- Design 6 questions, each with 3 descriptions mapped to 1/2/3 points
- Each description corresponds to a different treatment option preference
- Total score ranges guide the patient toward their value alignment
- Include interpretation table with score ranges and recommendations
- IMPORTANT: Include at least one "reality check" dimension (e.g., cost) to prevent the scoring from being one-directional
- Scoring is a GUIDE, not a prescription — always include disclaimer

**Knowledge Test (步驟三)**
- 7 questions minimum
- Format: 對/不對/我不確定 (True/False/Unsure)
- MUST have objectively correct answers — NO attitude or preference questions
- Include at least one myth-busting question (common misconception)
- Include answer key with brief explanations
- Cover: efficacy data, side effects, treatment process, key distinctions
- Suggest patients discuss with team if any answers were wrong

**Comparison Table**
- Side effects MUST be presented symmetrically (shared side effects in a joint row)
- Use neutral language — avoid making one option sound clearly superior
- Include: efficacy, side effects, treatment process, duration, cost, lifestyle impact, reversibility, psychological impact
- When options can be combined, add "是否可合併使用" row
- State evidence level for each option

**Step 4 — "Cannot Decide" Options**
- Minimum 3-4 specific reasons (discuss with doctor, discuss with family, need more time for specific concern, want to see/try something first)
- Tailor to the clinical context

### Word Document Technical Specs
- Paper: A4 (11906 × 16838 DXA)
- Font: Microsoft JhengHei (微軟正黑體) throughout
- Default text size: 22 half-points (11pt)
- Table text: 19-20 half-points
- Section titles: 28 half-points, bold, themed color
- Header: right-aligned, topic name, size 16, gray
- Footer: centered page number, size 16, gray
- Color theme: choose a distinct color per SDM topic (e.g., blue for urology, green for GI, rose for oncology)
- Tables: use DXA widths (never percentages), ShadingType.CLEAR, consistent borders
- Always validate after generation

---

## 3. Develop Mode (New SDM from Scratch)

### Workflow

**Phase 1: Research & Planning**
1. Search literature using Consensus:search (preferred) and web_search
   - Consensus:search for: systematic reviews, meta-analyses, RCTs
   - Filter: `study_types: ["systematic review", "meta-analysis", "rct"]`, `sjr_max: 2` for high-quality journals
   - web_search for: clinical guidelines (NCCN, AUA, EAU, etc.), Taiwan-specific data, NHI regulations
2. Summarize findings: key outcome data, evidence levels, knowledge gaps
3. Propose SDM structure:
   - Title and target population
   - Decision options (2-3 options, always consider "no treatment/observation")
   - Comparison table dimensions
   - Values clarification dimensions (check directional balance)
   - Knowledge test questions
   - Scoring system design (if requested)
4. Present plan to user for confirmation, including specific questions:
   - Local surgical data available?
   - Cost/NHI coverage details?
   - Specific technique variations?
   - Patient population nuances?

**Phase 2: Confirmation**
- User reviews and adjusts the plan
- Resolve all open questions before proceeding

**Phase 3: Production**
- Follow Enhance Mode specifications to produce .docx
- Include user's local data if provided

### Literature Search Strategy
```
Priority order:
1. Consensus:search — systematic reviews & meta-analyses (most recent 5 years)
2. Consensus:search — RCTs for specific outcome data
3. web_search — clinical practice guidelines
4. web_search — Taiwan-specific regulations, NHI coverage, local epidemiology
5. User-provided data (case series, institutional experience)
```

---

## 4. Scoring Mode (Auxiliary)

### Input
- A completed/enhanced SDM document (the content to score)
- The 醫策會 evaluation form (.xlsx): `醫療品質中心__223020-000-F-041-醫病共享決策輔助工具_PDAs_審查配分標準.xlsx`

### Process
1. Read xlsx skill at `/mnt/skills/public/xlsx/SKILL.md`
2. Load the xlsx with openpyxl (preserve all formatting, merged cells, formulas)
3. Fill Column F (scores) and Column G (justifications) for each row
4. Recalculate formulas with `scripts/recalc.py`
5. Verify totals
6. Copy to outputs and present

### Scoring Sheet Structure
```
Sheet: 評分表

壹、醫療專業 (Rows 4-17):
  Row 4-11: 內容呈現 (30pts) — Items 1-8
  Row 12-13: 幫助理解 (5pts) — Items 9-10
  Row 14-16: 研發過程 (20pts) — Items 11-13
  Row 17: 整體表現 (5pts)
  Row 18: Total (formula)

貳、民眾教育 (Rows 20-34):
  Row 20-31: 基本項目 — Items 1-12
  Row 33-34: 加分項目 — Items 13-14
  Row 35: Total (formula)

三、整體回饋 (Rows 36-39):
  Row 36: F = 長度 (太長/太短/適中)
  Row 37: F = 內容量 (太多/太少/適中)
  Row 38: F = 公平性 (是/否，偏向___)
  Row 39: F = 其他建議
```

### Scoring Principles
- Score based on the ENHANCED version (not the original)
- Be honest — don't inflate scores. Common deductions:
  - 研發過程 items (11-13): Most SDMs lose significant points here because they lack documented needs assessment, pilot testing, and search strategy. Score 1/5 if not documented.
  - 輔助素材 (item 10 in 貳): Score 1/3 if text/table only, no multimedia
- Justifications should be specific, citing concrete content from the SDM
- Note what was improved and what still needs work

---

## Context: User Profile

- Ming-Yu Hsieh (謝明諭), MD PhD, Pediatric Surgeon at CSMU Hospital (中山醫學大學附設醫院), Taichung, Taiwan
- Specialties relevant to SDM: pediatric surgery (MACE, circumcision, Hirschsprung), general surgery
- Has institutional surgical data for MACE (n=45, 2013-2025)
- SDM role: likely reviewer/developer for hospital quality committee and TAPS
- Language: SDM documents in Traditional Chinese; academic discussion can be bilingual

---

## Examples of Completed SDMs (for reference patterns)

1. **阿茲海默症單株抗體治療** — 3 options (new drug / traditional drug / non-pharma), evidence summary table with Phase III RCT data, 6-dimension values clarification, 7 knowledge questions
2. **老年乳癌放射治療** — 2 options (RT+endocrine / endocrine only), ARR/NNT presentation, disease background with Q&A format (local recurrence ≠ metastasis), hypofractionation options
3. **馬龍手術(MACE)** — 3 options (MACE / conservative / colostomy), scoring system (6 questions × 3 descriptions), local institutional data (n=45), innovative technique mention
4. **兒童包皮環切** — 3 options (traditional / stapler / observation), parent-oriented, scoring system with cost reality-check, 30% staple removal rate as key local data
