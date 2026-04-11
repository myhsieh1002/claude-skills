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

## Usage

In a Claude conversation, say:
> 請幫我處理SDM相關任務

or

> 請幫我修復 App Store 退件問題

Claude will automatically clone this repo and read the relevant SKILL.md.
