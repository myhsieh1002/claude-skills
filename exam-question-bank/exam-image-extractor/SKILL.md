---
name: exam-image-extractor
description: "Use this skill for extracting images from exam question PDFs and linking them to database question records. Handles: scanning PDFs for embedded images, filtering out small icons/bullets, mapping images to correct question numbers using text position analysis, handling cross-page images (top-of-page images belonging to previous page's last question), rendering image regions as PNG using PyMuPDF, multi-image compositing for questions with image-based options, and uploading to Supabase Storage with DB record update. Trigger on keywords: 題目圖片, extract images from PDF, 圖片擷取, 補圖, image extraction, 截取圖片."
---

# Exam Image Extractor Skill

## Overview

This skill extracts question-related images (diagrams, charts, X-rays, pathology slides, ECGs, etc.) from exam question PDFs, maps each image to its corresponding question in the database, and uploads them to cloud storage.

---

## Work Mode Detection

| User says | Mode |
|---|---|
| "幫我擷取PDF中的圖片" / "補全題庫圖片" | Full pipeline |
| "掃描哪些題目有圖片" / "scan for images" | Scan-only (dry run) |
| "只上傳圖片" / "upload extracted images" | Upload-only |

---

## Processing Pipeline

### Step 1: Scan PDFs for Images

Using `pdfplumber`, scan each page for embedded images:

```python
for page in pdf.pages:
    real_imgs = [
        img for img in page.images
        if img["width"] > 50 and img["height"] > 50  # filter icons/bullets
    ]
```

**Size threshold**: 50x50 pixels. Smaller images are typically:
- Checkbox marks or bullet points
- Decorative line elements
- PDF artifacts

### Step 2: Map Images to Question Numbers

For each image found, determine which question it belongs to:

**Case A — Image mid-page (most common)**:
```
Crop text above image position → find last question number
```

**Case B — Image at top of page (top ≈ 28-34)**:
```
No question text above → check previous page's last question number
This pattern occurs when: "...如圖所示：" ends a page,
and the actual figure appears at the top of the next page
```

**Case C — Multiple images per question**:
```
Same question number → group into single entry
Common for: option images (A/B/C/D are all images),
             multi-panel figures, before/after comparisons
```

### Step 3: Match to Database Records

Since PDF question numbers don't directly correspond to database IDs (due to skipped questions, reordering, or ID prefix differences), use **text-based matching**:

```python
# Build lookup from existing question data (JSON or DB)
# Key = source + normalized_question_text_prefix
# Use two tiers: 80-char prefix (primary), 40-char prefix (fallback)

def normalize_for_match(text):
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", "", text)

long_key = f"{source}|{category}|{normalize(question[:80])}"
short_key = f"{source}|{category}|{normalize(question[:40])}"
```

**Important**: If the database has been recategorized (e.g., "醫學（一）" → "解剖學"), match by `source + text_prefix` only, ignoring category.

### Step 4: Render Image Regions

Using **PyMuPDF (fitz)** for high-quality rendering:

```python
doc = fitz.open(pdf_path)
page = doc[page_index]
mat = fitz.Matrix(dpi / 72, dpi / 72)  # default dpi=200

# Compute bounding box encompassing all images for this question
clip = fitz.Rect(x0 - 5, y0 - 5, x1 + 5, y1 + 5)
pix = page.get_pixmap(matrix=mat, clip=clip)
pix.save("output.png")
```

**Multi-page stitching**: When images span two pages (e.g., question stem on page N, figure on page N+1), render each page's region separately and stitch vertically using PIL.

### Step 5: Upload and Update Database

```
1. Upload PNG to Supabase Storage: question-images/{app_id}/{question_id}.png
2. PATCH question record: SET image_name = '{question_id}.png'
```

---

## Common Image Types in Medical Exams

| Type | Typical size | Example |
|------|-------------|---------|
| Pathology slide | 200-400px wide | 組織切片圖 |
| X-ray / CT | 200-500px wide | 胸部X光 |
| ECG | 300-500px wide | 心電圖 |
| Chart / Table | 150-500px wide | 統計列聯表 |
| Chemical structure | 100-300px wide | NAD+ 結構式 |
| Clinical photo | 200-400px wide | 皮膚病灶 |
| Audiogram | 200-300px wide | 鼓室圖 |

---

## Edge Cases and Solutions

| Edge case | Solution |
|-----------|----------|
| Image at very top of page (top ≈ 28) | Check previous page's last question |
| All 4 options are images (A/B/C/D) | Group as single multi-image entry; note these questions may be missing from DB if converter skipped them |
| Duplicate images on same page (PDF artifact) | De-duplicate by position (same top/left) |
| Image spans page boundary | Detect via question continuity; stitch vertically |
| DB ID prefix differs from JSON (e.g., M1- vs MD-) | Always query DB for actual IDs; don't assume JSON IDs match |
| DB categories recategorized after import | Match by source + text prefix only, ignore category |
| Very small image but real content | Lower MIN_IMG_SIZE threshold if needed |

---

## Dependencies

- `pdfplumber` — PDF page analysis, image metadata extraction, text cropping
- `fitz` (PyMuPDF) — High-quality image region rendering
- `PIL` (Pillow) — Multi-page image stitching
- Supabase Storage API — Image upload
- Supabase REST API — Question record update

---

## Typical Results

Based on actual runs:
- 醫師第一階段 (38 PDFs): 32 real images → 28 matched + uploaded
- 醫師第二階段 (44 PDFs): 369 real images → 250 matched + uploaded
- Unmatched causes: image-only option questions not in DB, text normalization mismatches

---

## Related Skills
- `exam-pdf-parser` — Parse the same PDFs for question text (run first)
- `supabase-question-import` — Import questions before extracting images
