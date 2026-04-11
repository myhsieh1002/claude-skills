---
name: appstore-rejection-fix
description: Diagnose and fix App Store submission rejections for subscription apps (Guidelines 1.5, 2.1b, 3.1.2c, 2.3.2). Covers React form injection, IAP screenshot upload, Privacy Policy URL location, and resubmission flow.
---

# App Store Rejection Fix Skill

## Overview

This skill handles the four most common App Store rejection reasons for subscription-based apps. All steps use the Claude in Chrome MCP (`mcp__Claude_in_Chrome__*`) for browser interaction.

---

## Step 0: Diagnose the Rejection

1. Navigate to App Store Connect: `https://appstoreconnect.apple.com`
2. Go to Apps → [App Name] → left sidebar → App Store → [version] → 提交詳細資訊
3. Read the rejection reason(s). Map to the guidelines below.

---

## Guideline 1.5 — Support URL Invalid or Unreachable

**Symptom**: Support URL returns 404 or redirects incorrectly.

**Fix**:
1. Create a Notion support page: `[AppName] - Support` (include contact email, FAQ, cancellation info)
2. Use the current Notion domain: `iridescent-cub-5de.notion.site` (NOT `myhsieh1002.notion.site` — old domain is dead)
3. In App Store Connect → version page → 支援 URL field, inject the new URL using React native setter:
```javascript
const input = document.querySelector('input[name="supportUrl"]');
// or find the correct input by label
const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
nativeSetter.call(input, 'https://iridescent-cub-5de.notion.site/YOUR-SUPPORT-PAGE');
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
```
4. Save the version page.

---

## Guideline 2.1(b) — IAP Not Submitted for Review

**Symptom**: In-app purchases exist but were not submitted alongside the app version.

**Fix — all 4 steps required, missing any one will cause rejection**:

### Step 1: Add Subscription Group Localization
- App Store Connect → Subscriptions → [Group Name] → 本地化版本 → 建立
- Add 繁體中文 with a display name

### Step 2: Upload Review Screenshot for Each Subscription
- Go to each subscription item (Premium Monthly, Premium Quarterly, etc.)
- Upload a Paywall screenshot as the review screenshot
- **NOTE**: `file_upload` tool is blocked on App Store Connect. Use the clipboard base64 injection method (see `appstore-iap-upload` skill)

### Step 3: Link IAPs to the App Version
- Version page → scroll down to App 內購買項目 section → click to open modal
- **⚠️ SAFETY WARNING**: Do NOT use `querySelectorAll('input[type="checkbox"]')` to select all checkboxes — this also checks unrelated page checkboxes like "需要登入" (demoAccountRequired) and Game Center, causing validation errors
- Instead, identify IAP checkboxes specifically within the modal:
```javascript
// Safe: find only the IAP modal checkboxes
const modal = document.querySelector('[role="dialog"]') || document.querySelector('.modal');
const iapCheckboxes = modal ? modal.querySelectorAll('input[type="checkbox"]') : [];
iapCheckboxes.forEach(cb => { if (!cb.checked) cb.click(); });
```
- If you accidentally checked "需要登入", uncheck it:
```javascript
const demoCheck = document.querySelector('input[name="demoAccountRequired"]');
if (demoCheck && demoCheck.checked) demoCheck.click();
```

### Step 4: Trigger Resubmission
- On the version inflight page, click **"更新審查內容"** (NOT "重新提交至 App 審查" — that button is often disabled)
- A page should appear; confirm submission
- Status should change to "準備審查" ✅

---

## Guideline 3.1.2(c) — Missing EULA or Privacy Policy

**Two separate fixes required**:

### Fix A: Add EULA Link to App Description
- Version page → App 描述 field
- Append to the end of the description:
```
使用條款（EULA）：https://www.apple.com/legal/internet-services/itunes/dev/stdeula/
```
- Use React native setter if direct editing doesn't trigger save:
```javascript
const textarea = document.querySelector('textarea[name="description"]');
const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
nativeSetter.call(textarea, newValue);
textarea.dispatchEvent(new Event('input', { bubbles: true }));
```

### Fix B: Update Privacy Policy URL in App Privacy Section
- **⚠️ LOCATION**: This field is NOT on the version page and NOT on the App Info page
- Path: Left sidebar → App Store → **信任與安全** → **App 隱私權** → 編輯
- This opens a dialog. Find the Privacy Policy URL input:
```javascript
const input = document.getElementById('privacyPolicyUrl');
const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
nativeSetter.call(input, 'https://iridescent-cub-5de.notion.site/AppName-Privacy-Policy-PAGEID');
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
```
- Then click the **儲存** button in the dialog (find via ref or `document.querySelector('button[type="submit"]')` within the dialog)

**Privacy Policy Notion page**: Must be a real, accessible page. Use domain `iridescent-cub-5de.notion.site`.

---

## Guideline 2.3.2 — Duplicate IAP Promotional Images

**Symptom**: Premium Monthly and Premium Quarterly have identical 1024×1024 promotional images.

**Fix**:
- Go to each subscription item → 影像 section
- Delete the promotional image:
```javascript
// Find the promotional image and its delete button
const imgEl = document.querySelector('img[src*="1024x1024bb"]');
let el = imgEl;
let deleteBtn = null;
for (let i = 0; i < 8; i++) {
  el = el?.parentElement;
  if (!el) break;
  const btn = Array.from(el.querySelectorAll('button')).find(b => b.textContent.trim() === '刪除');
  if (btn) { deleteBtn = btn; break; }
}
deleteBtn?.click();
// Confirm in the dialog that appears
```
- Confirm deletion in the dialog
- **Prevention**: Either leave promotional images blank (safe, never rejected), or use a different 1024×1024 image for each subscription tier

---

## Final Resubmission Checklist

Before clicking submit, verify:
- [ ] Support URL is reachable (open in incognito to confirm)
- [ ] Privacy Policy URL is reachable (open in incognito)
- [ ] EULA link is in the App Description
- [ ] Each IAP has a review screenshot uploaded
- [ ] IAP subscription group has 繁體中文 localization
- [ ] IAPs are linked to the version (checked in the IAP modal)
- [ ] "需要登入" checkbox is NOT checked (unless app requires login)
- [ ] IAP promotional images are either blank or unique per tier
- [ ] Version page is saved before submitting

---

## Technical Notes

### React Form Fields on App Store Connect
App Store Connect uses React-controlled inputs. Direct `.value =` assignment won't trigger React's onChange handlers. Always use:
```javascript
const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
nativeSetter.call(inputElement, newValue);
inputElement.dispatchEvent(new Event('input', { bubbles: true }));
inputElement.dispatchEvent(new Event('change', { bubbles: true }));
```

### Common Input IDs/Names
- Support URL: `input[name="supportUrl"]` or find by adjacent label text
- Privacy Policy URL: `document.getElementById('privacyPolicyUrl')` (only in App 隱私權 dialog)
- IAP review screenshot: `input[id^="iap_review_info_"]`
- Demo account required: `input[name="demoAccountRequired"]`

### Resubmission Button States
- "重新提交至 App 審查" — often disabled after first submission
- "更新審查內容" — always works; use this to trigger review of updated content
