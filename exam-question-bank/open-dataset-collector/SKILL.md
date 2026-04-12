---
name: open-dataset-collector
description: "Use this skill for collecting and processing open-source exam question datasets from external sources. Handles: downloading datasets from HuggingFace (e.g., MedQA), parsing official sample exam PDFs (e.g., USMLE), keyword-based heuristic classification of questions into categories/stages, merging multiple question sources with unified ID formatting, and copyright/licensing considerations. Trigger on keywords: 開源題庫, open dataset, HuggingFace, MedQA, 蒐集題目, collect questions, 免費資源, free resources, download questions."
---

# Open Dataset Collector Skill

## Overview

This skill collects exam questions from publicly available sources — academic datasets, official sample exams, and open educational resources — and converts them into the standardized JSON format for database import.

---

## Work Mode Detection

| User says | Mode |
|---|---|
| "幫我蒐集免費的題目" / "collect open questions" | Research + collect |
| "下載MedQA資料集" / "download from HuggingFace" | Direct download |
| "解析官方樣題" / "parse sample exam PDF" | PDF parsing |
| "分類題目" / "classify questions" | Classification only |

---

## Supported Data Sources

### 1. HuggingFace Datasets

**MedQA** (primary medical exam source):
- Repository: `GBaker/MedQA-USMLE-4-options`
- Size: ~11,450 questions (USMLE-style, 4 options each)
- Format: JSON with fields `question`, `answer`, `options`, `meta_info`
- License: Academic use

```python
# Download via HuggingFace datasets API
from datasets import load_dataset
ds = load_dataset("GBaker/MedQA-USMLE-4-options", split="train+test+validation")

# Or download raw JSON directly
# Save combined data as medqa_all.json
```

**Other potential datasets**:
- `medmcqa` — Indian medical exam (AIIMS/PGI)
- `pubmedqa` — PubMed-based QA (yes/no/maybe format, less suitable)
- `mmlu` — Multi-task benchmark with medical subsets

### 2. Official Sample Exams

**USMLE Sample Questions**:
- Source: USMLE.org official practice materials (free PDF download)
- Step 1: ~120 questions across 6 blocks
- Step 2 CK: ~120 questions across 3 blocks
- Format: Clinical vignettes with (A)-(E) options, answer key at end

**Parsing approach**:
```python
def parse_questions_from_pdf(pdf, q_start_page, q_end_page):
    # Extract text from question pages
    # Split by question number pattern: \d+\.
    # For each question: separate stem from options (A)-(E/F/G)
    # Handle multi-page questions

def parse_answer_key(pdf):
    # Usually on last or second-to-last page
    # Format: "1. A  2. C  3. B ..."
    # Return dict: {question_number: answer_letter}
```

### 3. Other Sources (research before using)

- Taiwan 考選部 historical exams (public domain)
- NBME practice exams (check terms of use)
- OpenStax textbook questions (CC-BY licensed)
- Anki shared decks (varies by deck)

---

## Question Classification

### Heuristic Keyword Classification

For datasets without pre-labeled categories (e.g., MedQA → Step 1 vs Step 2):

```python
STEP1_KEYWORDS = {
    # Basic science / foundational
    "mechanism", "pathogenesis", "receptor", "enzyme", "mutation",
    "gene", "chromosome", "histology", "embryology", "biochemistry",
    "pharmacokinetics", "pharmacodynamics", "molecular", "cellular",
    # Specific to Step 1 topics
    "Krebs cycle", "glycolysis", "p53", "apoptosis", "necrosis",
}

STEP2_KEYWORDS = {
    # Clinical management / next step
    "next best step", "most appropriate management", "initial treatment",
    "screening", "counseling", "discharge", "follow-up", "referral",
    # Clinical settings
    "emergency department", "presents to clinic", "postoperative",
}

def classify(question_text):
    text_lower = question_text.lower()
    s1_score = sum(1 for kw in STEP1_KEYWORDS if kw in text_lower)
    s2_score = sum(1 for kw in STEP2_KEYWORDS if kw in text_lower)
    return "Step 1" if s1_score > s2_score else "Step 2"
```

### Category Assignment

After Step classification, assign detailed categories:

**Step 1 categories**:
| Category | Keywords |
|----------|----------|
| Pharmacology | drug, receptor, inhibitor, agonist, antagonist |
| Biochemistry & Nutrition | enzyme, substrate, vitamin, cofactor, metabolic |
| Pathology | biopsy, histology, microscopy, neoplasm, tumor |
| Microbiology & Immunology | bacteria, virus, immune, antibody, infection |
| Physiology | pressure, flow, cardiac output, renal, membrane potential |
| Anatomy & Histology | nerve, artery, muscle, bone, histologic |
| Genetics | mutation, chromosome, inheritance, autosomal, allele |
| Behavioral Sciences | prevalence, incidence, odds ratio, study design |

**Step 2 CK categories**:
| Category | Keywords |
|----------|----------|
| Internal Medicine | diabetes, hypertension, chest pain, dyspnea |
| Surgery | appendectomy, cholecystectomy, surgical, incision |
| Pediatrics | infant, child, neonate, growth, development |
| Obstetrics & Gynecology | pregnant, gestational, cervical, menstrual |
| Psychiatry | depression, anxiety, schizophrenia, bipolar |
| Emergency Medicine | emergency, acute, trauma, resuscitation |

---

## Output JSON Format

Unified format matching `exam-pdf-parser` output:

```json
{
  "id": "S1-MQ-00001",
  "question": "A 58-year-old woman who died of...",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "answer": 0,
  "explanation": "",
  "category": "General Principles",
  "source": "MedQA",
  "difficulty": 2,
  "tags": ["medqa", "step1"]
}
```

**ID format conventions**:
| Source | Step 1 | Step 2 |
|--------|--------|--------|
| Official sample | `S1-SAMPLE-NNN` | `S2-SAMPLE-NNN` |
| MedQA | `S1-MQ-NNNNN` | `S2-MQ-NNNNN` |

---

## Copyright and Licensing Considerations

| Source | License | Safe to use |
|--------|---------|-------------|
| MedQA (HuggingFace) | Academic/research | Yes for development/reference |
| USMLE official samples | Free public download | Yes for development/reference |
| NBME practice exams | Paid, copyrighted | No — do not scrape |
| Published textbook questions | Copyrighted | No — unless CC-licensed |
| User-created original questions | User owns | Yes |

**Key principle**: Collect freely available resources for reference/development. For production question banks, create original questions inspired by (but not copied from) these references.

---

## Dependencies

- `datasets` (HuggingFace) — For downloading datasets (optional, can use direct JSON download)
- `pdfplumber` — For parsing official sample PDFs
- `requests` or `urllib` — For downloading files
- Python standard library: `json`, `re`

---

## Related Skills
- `exam-pdf-parser` — For parsing downloaded PDF sources
- `supabase-question-import` — For importing collected questions to database
