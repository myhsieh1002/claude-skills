---
name: exam-pdf-parser
description: "Use this skill for parsing exam question PDFs into structured JSON. Covers Taiwan national exam PDFs (考選部), USMLE sample PDFs, and similar multiple-choice exam formats. Handles: extracting question text with options from PDF pages, parsing answer key PDFs (standard tabular format with 題號/答案 rows), CJK text cleanup (removing spurious spaces from PDF extraction), full-width/half-width normalization, question numbering, and outputting standardized JSON. Trigger on keywords: 考題解析, PDF轉JSON, 題庫轉換, parse exam PDF, extract questions from PDF, 答案解析, 考選部."
---

# Exam PDF Parser Skill

## Overview

This skill converts exam question PDFs into structured JSON format suitable for database import. It handles the full pipeline from raw PDF to clean, validated question records.

Primarily designed for:
- **Taiwan national exams** (考選部 format): 醫師、牙醫、藥師、護理師 etc.
- **USMLE sample questions**: Clinical vignette style with (A)-(E) options
- **Any standard multiple-choice exam PDF** with numbered questions and lettered options

---

## Work Mode Detection

| User says | Mode |
|---|---|
| "幫我解析這份考題PDF" / "把PDF轉成JSON" | Full pipeline |
| "只解析答案" / "parse answer key" | Answer-only extraction |
| "檢查解析結果" / "驗證題目數量" | Validation mode |

---

## Input Requirements

### Question PDF format (考選部 standard)
- Questions numbered sequentially: `1.` `2.` ... `100.` (or `1．` `2．` with full-width period)
- Options labeled: `A.` `B.` `C.` `D.` (sometimes `E.`)
- May contain embedded images (handled separately by exam-image-extractor skill)
- Header page with exam metadata (year, subject, exam code)

### Answer PDF format
- Tabular layout with rows:
  ```
  題號  01  02  03  ...  20
  答案   Ｃ   Ａ   Ｄ  ...  Ａ
  ```
- Full-width letters (Ａ-Ｅ) common
- `#` marks disputed/voided questions (skip these)
- Prefer `更正答案` (corrected) over `答案` (original) when both exist

### Filename convention (考選部)
```
{ROC_YEAR}_{EXAM_CODE}_c{CERT_CODE}_s{SUBJECT_CODE}_{SUBJECT_NAME}.pdf
```
Example: `113_113020_c301_s11_醫學（一）（包括...）.pdf`
- ROC year: first 3 digits (e.g., 113 = AD 2024)
- Exam code suffix ≤ 050 → 第一次, > 050 → 第二次
- Cert code: c301=醫師第一階段, c302=醫師第二階段, c304=牙醫 etc.

---

## Output JSON Format

Each question record:
```json
{
  "id": "{PREFIX}-{AD_YEAR}-{SEQ:04d}",
  "question": "Question stem text (cleaned)",
  "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
  "answer": 0,
  "explanation": "",
  "category": "Subject category name",
  "source": "113年第一次醫師國考",
  "difficulty": 2,
  "tags": ["113年", "第一次"]
}
```

Key fields:
- `answer`: 0-based index (A=0, B=1, C=2, D=3)
- `options`: Always 4 elements (pad with empty string if needed, trim to 4 if 5 options)
- `id`: Unique, deterministic, sortable

---

## Processing Pipeline

### Step 1: Build Answer Lookup
```
For each answer PDF (prefer 更正答案 over 答案):
  1. Extract text from all pages
  2. Normalize full-width letters → ASCII (Ａ→A, Ｂ→B...)
  3. Find 題號/答案 row pairs
  4. Build dict: {question_number: answer_letter}
  5. Skip questions marked with # (disputed)
```

### Step 2: Extract Questions from PDF
```
For each question PDF:
  1. Extract text from all pages using pdfplumber
  2. Identify question boundaries using regex: ^\s*(\d{1,3})\s*[\.．、]
  3. Split question stem from options using option markers: \n([A-E])[\.．、]\s*
  4. Clean CJK spaces (spurious spaces between CJK characters from PDF extraction)
  5. Match answers from lookup
  6. Generate sequential IDs
```

### Step 3: CJK Text Cleanup
Critical for Taiwan exam PDFs where pdfplumber inserts spaces between CJK characters:
```python
_CJK_RE = re.compile(
    r"([\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef])\s+"
    r"([\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef（）【】「」])"
)
# Apply repeatedly until stable:
while prev != text:
    prev = text
    text = _CJK_RE.sub(r"\1\2", text)
```

### Step 4: Validation
After parsing, verify:
- Question count matches expected (typically 80 or 100 per subject)
- All questions have valid answers (0-3)
- All questions have exactly 4 options with non-empty text
- No duplicate IDs
- Source/category fields are consistent

---

## Common Issues and Solutions

| Issue | Symptom | Fix |
|-------|---------|-----|
| Full-width digits/letters | Options not detected | Normalize with NFKC + explicit mapping |
| Mixed-width parentheses | `（3)` not matched | Use character class `[（(]` `[）)]` |
| Wrapped text across lines | Incomplete question stems | Forward-propagation text assembly |
| Questions with image-only options | 0 options parsed, skipped | Expected — flag for manual review |
| Header/footer text leaking | Extra text in questions | Filter by known header patterns |

---

## Dependencies

- `pdfplumber` — PDF text extraction
- `openpyxl` — Excel file reading (if intermediate Excel format used)
- `unicodedata` — NFKC normalization

---

## Example Usage

```python
# Typical invocation
python3 convert_to_json.py --input-dir input --json-dir json_output

# The script will:
# 1. Parse all answer PDFs in input/
# 2. Parse all question PDFs in input/
# 3. Match answers to questions
# 4. Output per-year JSON + combined JSON to json_output/
```

---

## Related Skills
- `exam-image-extractor` — Extract images from the same PDFs
- `supabase-question-import` — Import the output JSON to Supabase
