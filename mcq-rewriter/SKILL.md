---
name: mcq-rewriter
description: "Analyze, evaluate, and rewrite medical or health sciences multiple-choice question (MCQ) banks based on learning science principles (the Practice-Driven Learning Loop model). Use this skill whenever the user uploads an MCQ bank (Excel, CSV, Word, or PDF) and wants to: analyze topic coverage and question quality, rewrite questions to meet evidence-based design standards, generate explanatory feedback for each item, add classification tags and metadata, create interleaved question sequences, or produce a restructured item bank. Also trigger when the user mentions 'question bank', 'item bank', 'MCQ rewrite', 'question improvement', 'item writing', 'test item analysis', 'PLL model', or asks to improve exam questions for any health profession. Works for any medical specialty or health science discipline."
---

# MCQ Rewriter — Practice-Driven Learning Loop (PLL) Item Bank Skill

## Overview

This skill transforms raw MCQ banks into learning-science-optimized item banks based on the **Practice-Driven Learning Loop (PLL) model**, which integrates five learning theories: schema theory, retrieval practice, chunking, interleaving, and desirable difficulties.

## When to Use

- User uploads an MCQ file (Excel/CSV/Word/PDF) and wants quality analysis or rewriting
- User asks to "improve", "rewrite", "upgrade", or "redesign" exam questions
- User wants to add clinical vignettes, explanatory feedback, or classification tags to existing items
- User wants to reorganize question sequence for interleaved practice
- User mentions PLL model, item writing, NBME standards, or evidence-based assessment design

## Workflow

The skill operates in **four modes**. Ask the user which mode they need, or infer from context:

### Mode 1: ANALYZE — Audit the existing item bank
### Mode 2: REWRITE — Transform items to PLL standards
### Mode 3: GENERATE — Create new items from topic specifications
### Mode 4: SEQUENCE — Arrange items for optimal interleaved practice

---

## Mode 1: ANALYZE

### Step 1: Read the input file
- Read the uploaded file from `/mnt/user-data/uploads/`
- For Excel/CSV: identify column mappings (stem, options, answer, feedback, tags)
- For Word/PDF: parse question blocks using pattern recognition
- If column mapping is ambiguous, ask the user to confirm

### Step 2: Classify each item on 7 quality dimensions

For each question, evaluate and score (0–2) on these dimensions:

| Dimension | 0 = Absent | 1 = Partial | 2 = Full |
|-----------|-----------|-------------|----------|
| **Clinical vignette** | No context; bare fact question | Brief context but incomplete scenario | Full clinical vignette with age, presentation, findings |
| **Cognitive level** | Pure recall (Bloom: Remember) | Understanding/interpretation | Application or higher (Bloom: Apply/Analyze) |
| **Cover test passable** | Cannot answer without seeing options | Partially answerable | Fully answerable before seeing options |
| **Distractor quality** | Implausible or heterogeneous options | Mixed quality; some fillers | All homogeneous, plausible, reflecting common errors |
| **Cue-free** | Contains grammatical cues or longest-option bias | Minor cue issues | No detectable cues |
| **Feedback quality** | No feedback or answer-only | Correct answer with brief explanation | Elaborated feedback explaining why correct AND why each distractor is wrong |
| **Classification tags** | No tags | Partial tags (topic only) | Full tags: topic, mechanism, organ system, difficulty level |

**Total PLL Quality Score**: Sum of 7 dimensions = 0–14

**Rating bands**:
- 0–4: **Needs full rewrite** (typically fact-recall items with no vignette)
- 5–8: **Needs significant revision** (has some elements but missing key PLL components)
- 9–11: **Minor revision needed** (good base, needs feedback or tag enhancement)
- 12–14: **PLL-compliant** (meets all standards)

### Step 3: Generate analysis report

Output an Excel file with:
- **Sheet 1 "Summary"**: Total items, score distribution histogram, topic coverage matrix, top improvement priorities
- **Sheet 2 "Item Analysis"**: One row per item with all 7 dimension scores + total + specific improvement notes
- **Sheet 3 "Topic Map"**: Extracted topic taxonomy with item counts per topic

Also provide a narrative summary in chat.

---

## Mode 2: REWRITE

### Step 1: Read and analyze (same as Mode 1, Steps 1–2)

### Step 2: Rewrite each item following the 5 PLL Design Principles

Read the detailed design principles from `references/pll-design-principles.md` before rewriting.

For each item, apply these transformations:

#### Principle 1 — Stem Design (Schema Activation)
- If no clinical vignette exists: CREATE one with age, sex, chief complaint, relevant history, key findings
- If vignette is incomplete: ENHANCE with missing elements
- Ensure stem passes the **cover test** (answerable without seeing options)
- Remove irrelevant information that adds cognitive load without changing the answer
- For advanced learners: optionally add contextual noise that simulates real clinical complexity

#### Principle 2 — Distractor Design (Cognitive Discrimination)
- Ensure all options are **homogeneous** (same category: all diagnoses, all drugs, all procedures)
- Ensure all distractors are **plausible** — each should reflect a common misconception or reasoning error
- Remove fillers, "none of the above", "all of the above"
- Remove grammatical cues, longest-option bias, absolute terms ("always", "never")
- Aim for 4 options (1 correct + 3 functional distractors); 3 is acceptable if a 4th plausible distractor cannot be created

#### Principle 3 — Feedback Design (Schema Reorganization)
Generate structured feedback for EVERY item with these components:

```
[CORRECT ANSWER EXPLANATION]
Why (A) is correct: [Mechanism/reasoning explanation]

[DISTRACTOR EXPLANATIONS]
Why (B) is incorrect: [When B would be correct / why it doesn't apply here]
Why (C) is incorrect: [When C would be correct / why it doesn't apply here]
Why (D) is incorrect: [When D would be correct / why it doesn't apply here]

[CONCEPT FRAMEWORK]
Topic: [Disease category]
Core mechanism: [Pathophysiology/pharmacology principle]
Key discrimination point: [What distinguishes the correct answer from the closest distractor]

[ERROR TYPE if answering incorrectly]
Most common error: [Concept confusion / Knowledge gap / Reasoning error]
```

#### Principle 4 — Classification Tags
Add these metadata fields to every item:

| Tag | Description | Example |
|-----|-------------|---------|
| `topic_primary` | Main topic | Acute appendicitis |
| `topic_secondary` | Related subtopics | Acute abdomen, surgical emergency |
| `organ_system` | Organ system | Gastrointestinal |
| `mechanism_type` | Pathophysiology category | Inflammatory / Obstructive / Vascular / Neoplastic / Infectious / Autoimmune |
| `cognitive_level` | Bloom's level | Remember / Understand / Apply / Analyze |
| `miller_level` | Miller's pyramid | Knows / Knows How / Shows How |
| `difficulty_estimate` | Estimated difficulty | Easy / Medium / Hard |
| `discrimination_cluster` | Group of easily confused diagnoses | [Intussusception, Enterocolitis, Meckel's diverticulum] |

#### Principle 5 — Difficulty Calibration
- Flag items where difficulty may be misaligned with intended audience
- Suggest difficulty variants: for each core concept, note where an easier or harder version could be created (e.g., classic presentation → atypical presentation → complication management)

### Step 3: Output the rewritten item bank

**Primary output: Excel (.xlsx)** with these sheets:
- **Sheet 1 "Items"**: Columns: `item_id`, `stem`, `option_a`, `option_b`, `option_c`, `option_d`, `correct_answer`, `feedback_correct`, `feedback_a`, `feedback_b`, `feedback_c`, `feedback_d`, `concept_framework`, `error_type`, `topic_primary`, `topic_secondary`, `organ_system`, `mechanism_type`, `cognitive_level`, `miller_level`, `difficulty_estimate`, `discrimination_cluster`, `original_item_id`, `revision_notes`
- **Sheet 2 "Quality Comparison"**: Side-by-side before/after PLL scores for each item
- **Sheet 3 "Topic Map"**: Updated topic taxonomy

**Secondary output: JSON (.json)** with the same data structured for API consumption:
```json
{
  "metadata": {
    "generated_date": "YYYY-MM-DD",
    "total_items": N,
    "pll_version": "1.0",
    "source_file": "original_filename"
  },
  "items": [
    {
      "item_id": "001",
      "stem": "...",
      "options": [
        {"label": "A", "text": "...", "is_correct": true},
        {"label": "B", "text": "...", "is_correct": false},
        ...
      ],
      "feedback": {
        "correct_explanation": "...",
        "distractor_explanations": {"A": "...", "B": "...", ...},
        "concept_framework": "...",
        "common_error_type": "..."
      },
      "tags": {
        "topic_primary": "...",
        "organ_system": "...",
        "mechanism_type": "...",
        "cognitive_level": "...",
        "miller_level": "...",
        "difficulty_estimate": "...",
        "discrimination_cluster": [...]
      }
    }
  ]
}
```

---

## Mode 3: GENERATE

When the user provides topic specifications (not an existing item bank), generate new items from scratch.

### Step 1: Clarify specifications
- What topics/diseases/systems to cover?
- Target audience (medical student, resident, attending)?
- Number of items per topic?
- Desired cognitive level distribution?

### Step 2: Generate items
- Follow ALL Principle 1–5 standards from Mode 2
- For each topic, generate items at multiple difficulty levels when possible
- Ensure discrimination clusters are represented (i.e., generate items that test similar-but-different conditions)

### Step 3: Output in same format as Mode 2

---

## Mode 4: SEQUENCE

Given an item bank (original or rewritten), generate an optimized practice sequence.

### Sequencing rules (based on interleaving + spacing literature):

1. **No two consecutive items from the same topic** (interleaving)
2. **Discrimination cluster items should appear within 3–5 items of each other** (discriminative contrast)
3. **Same concept reappears at expanding intervals**: first at ~5 items apart, then ~15, then ~30 (spacing effect)
4. **Difficulty should oscillate**, not monotonically increase — mix easy/medium/hard to maintain engagement and prevent cognitive overload
5. **High-confusion pairs should be non-adjacent but close** (e.g., intussusception item at position 7, enterocolitis at position 10)

### Output:
- Excel with a "Sequence" sheet showing the recommended practice order with position numbers
- JSON with `sequence_order` field added to each item

---

## Important Reminders

- **Language**: Match the language of the original item bank. If the original is in Chinese, rewrite in Chinese with English medical terms in parentheses where appropriate. If in English, output in English.
- **Medical accuracy**: Do not invent clinical facts. If unsure about a medical detail, flag it for the user to verify.
- **Preserve original intent**: When rewriting, maintain the core knowledge point the original item was testing. The transformation is in HOW it's tested, not WHAT is tested.
- **Batch processing**: For large item banks (>50 items), process in batches of 20 and confirm with the user between batches.
- **Always read `references/pll-design-principles.md`** before starting any rewrite work — it contains the full theoretical rationale and detailed examples for each principle.

---

## Dependencies

- `openpyxl` (Python) or `xlsx` npm package for Excel I/O
- `pandas` for data manipulation if using Python
- Standard file reading tools for Word/PDF input
