# Claude Skills

Custom SKILL.md files for use with Claude (claude.ai / Claude Desktop).

These skills provide standardized workflows and quality frameworks that Claude
can load at the beginning of a conversation via `git clone`.

## Available Skills

| Skill | Description |
|-------|-------------|
| `sdm-development/` | 醫病共享決策 (Shared Decision Making) — Review, enhance, develop, and score SDM decision aids for hospital use |
| `appstore-rejection-fix/` | App Store 退件修復 — Diagnose and fix rejections for Guidelines 1.5, 2.1b, 3.1.2c, 2.3.2; includes React form injection, resubmission flow, and pre-submission checklist |
| `appstore-iap-upload/` | IAP 審查截圖上傳 — Clipboard base64 injection workaround for uploading IAP review screenshots to App Store Connect (file_upload is blocked) |
| `exam-question-bank/exam-pdf-parser/` | 考題PDF解析 — Parse exam question PDFs (Taiwan national exams, USMLE) into structured JSON with answer key matching and CJK text cleanup |
| `exam-question-bank/exam-image-extractor/` | 題目圖片擷取 — Extract images from exam PDFs, map to question records via text matching, and upload to Supabase Storage |
| `exam-question-bank/supabase-question-import/` | 題庫匯入Supabase — Import structured question JSON into Supabase with batch upsert, AES-256-GCM encryption, and image handling |
| `exam-question-bank/open-dataset-collector/` | 開源題庫蒐集 — Collect exam questions from HuggingFace datasets, official sample PDFs, and other open sources |

## Usage

In a Claude conversation, say:
> 請幫我處理SDM相關任務

or

> 請幫我修復 App Store 退件問題

or for exam question bank tasks:
> 幫我解析考題PDF / 匯入題庫到Supabase / 擷取題目圖片 / 蒐集開源題目

Claude will automatically clone this repo and read the relevant SKILL.md.
