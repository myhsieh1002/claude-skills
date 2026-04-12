---
name: supabase-question-import
description: "Use this skill for importing exam question JSON data into Supabase. Handles: creating apps and categories in Supabase, batch upserting questions (100/batch), AES-256-GCM encryption of explanation fields, uploading question images to Supabase Storage bucket, updating image_name on question records, and verifying import results. Trigger on keywords: 匯入Supabase, import to Supabase, 題庫匯入, upload questions, Supabase import, 上傳題庫."
---

# Supabase Question Import Skill

## Overview

This skill imports structured question JSON (produced by `exam-pdf-parser` or `open-dataset-collector`) into a Supabase-backed question bank system. It manages the full lifecycle: creating apps, categories, upserting questions, encrypting sensitive fields, and handling image uploads.

---

## Work Mode Detection

| User says | Mode |
|---|---|
| "匯入題庫到Supabase" / "import questions" | Full import |
| "只建立app和categories" | Setup only |
| "上傳圖片到Storage" | Image upload only |
| "驗證匯入結果" | Verification |
| "--dry-run" | Dry run (no writes) |

---

## Supabase Schema

### `apps` table
```sql
id          TEXT PRIMARY KEY,   -- e.g., "mdexam1", "usmle1dev"
display_name TEXT,              -- e.g., "醫師國考第一階段", "USMLE 1（開發用）"
total_questions INTEGER,
version     TEXT,               -- e.g., "1.0"
min_app_version TEXT            -- e.g., "1.0.0"
```

### `categories` table
```sql
app_id      TEXT REFERENCES apps(id),
name        TEXT,               -- e.g., "醫學（一）", "Internal Medicine"
sort_order  INTEGER
```

### `questions` table
```sql
id                    TEXT PRIMARY KEY,  -- e.g., "M1-2024-0001"
app_id                TEXT REFERENCES apps(id),
question              TEXT,             -- Question stem
options               JSONB,           -- ["Option A", "Option B", "Option C", "Option D"]
answer                INTEGER,         -- 0-based index
explanation_encrypted TEXT,            -- AES-256-GCM encrypted, base64 encoded
category              TEXT,
subcategory           TEXT,
difficulty            INTEGER,         -- 1-5 scale, default 2
tags                  JSONB,           -- ["113年", "第一次"]
image_name            TEXT,            -- e.g., "M1-2024-0001.png" or NULL
source                TEXT,            -- e.g., "113年第一次醫師國考"
version               TEXT,
is_published          BOOLEAN DEFAULT TRUE
```

### `question-images` Storage bucket
```
question-images/
├── mdexam1/
│   ├── M1-2024-0001.png
│   └── ...
├── mdexam2/
│   └── ...
└── carlic/
    └── ...
```

---

## Processing Pipeline

### Step 1: Ensure App Exists

```python
# Check if app exists
GET /rest/v1/apps?id=eq.{app_id}&select=id

# Create if not exists
POST /rest/v1/apps
{
  "id": "mdexam1",
  "display_name": "醫師國考第一階段",
  "total_questions": 0,
  "version": "1.0",
  "min_app_version": "1.0.0"
}
```

### Step 2: Ensure Categories Exist

```python
# Check existing categories
GET /rest/v1/categories?app_id=eq.{app_id}&select=name

# Create missing categories
POST /rest/v1/categories
{ "app_id": "mdexam1", "name": "醫學（一）", "sort_order": 1 }
```

### Step 3: Batch Upsert Questions

Process in batches of **100** with merge-duplicates:

```python
POST /rest/v1/questions
Headers:
  Prefer: resolution=merge-duplicates,return=representation

Body: [array of up to 100 question objects]
```

Each question object:
```python
{
    "id": q["id"],
    "app_id": app_id,
    "question": q["question"],
    "options": q["options"],        # JSON array
    "answer": q["answer"],          # 0-based integer
    "explanation_encrypted": encrypt(q.get("explanation", "")),
    "category": q["category"],
    "subcategory": q.get("subcategory", ""),
    "difficulty": q.get("difficulty", 2),
    "tags": q.get("tags", []),      # JSON array
    "image_name": None,             # Set later by image extractor
    "source": q.get("source"),
    "version": q.get("version", "1.0"),
    "is_published": True,
}
```

### Step 4: Encrypt Explanations

Using AES-256-GCM matching the Node.js frontend implementation:

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import secrets, base64

def encrypt(plaintext: str) -> str:
    if not plaintext:
        return ""
    key_bytes = bytes.fromhex(ENCRYPTION_KEY)  # 32-byte hex key
    iv = secrets.token_bytes(12)               # 96-bit IV
    ciphertext = AESGCM(key_bytes).encrypt(iv, plaintext.encode("utf-8"), None)
    # ciphertext includes 16-byte auth tag at the end
    return base64.b64encode(iv + ciphertext).decode("ascii")
```

### Step 5: Upload Images (optional)

```python
# Upload to Storage
POST /storage/v1/object/question-images/{app_id}/{image_name}
Headers:
  Content-Type: image/png
  x-upsert: true
Body: <binary PNG data>

# Update question record
PATCH /rest/v1/questions?id=eq.{question_id}
{ "image_name": "M1-2024-0001.png" }
```

---

## Authentication

All requests require:
```
Headers:
  apikey: {SUPABASE_SERVICE_KEY}
  Authorization: Bearer {SUPABASE_SERVICE_KEY}
  Content-Type: application/json
```

Use the **service_role** key (not anon key) for write operations.

---

## Verification Checklist

After import, verify:

1. **Question count**: `GET /rest/v1/questions?app_id=eq.{app_id}&select=id` with `Prefer: count=exact`
2. **Category distribution**: Check each category has expected count
3. **Image linkage**: `GET /rest/v1/questions?app_id=eq.{app_id}&image_name=neq.null&select=id`
4. **Storage files**: `GET /storage/v1/object/info/question-images/{app_id}/{image_name}`
5. **Encryption**: Decrypt a sample explanation to verify round-trip

---

## Known App IDs

| App ID | Display Name | Question Count |
|--------|-------------|----------------|
| mdexam1 | 醫師國考第一階段 | 3,704 |
| mdexam2 | 醫師國考第二階段 | 3,512 |
| carlic | 汽車駕照筆試 | 1,484 |
| motorlic | 機車駕照筆試 | 990 |
| usmle1dev | USMLE 1（開發用） | 1,471 |
| usmle2dev | USMLE 2（開發用） | 10,217 |

---

## Dependencies

- `cryptography` — AES-256-GCM encryption
- `urllib.request` — HTTP requests (no external dependencies needed)
- Python standard library: `json`, `base64`, `secrets`, `time`

---

## Related Skills
- `exam-pdf-parser` — Produces the JSON input for this skill
- `exam-image-extractor` — Extracts and uploads images after questions are imported
- `open-dataset-collector` — Another source of JSON input
