---
status: completed
baseline_commit: NO_VCS (git not available)
version: 1.0.0
date: 2026-03-30
title: Bug Screenshot Recognition - AI-powered bug screenshot analysis
description: Upload bug screenshots and use Baidu AI Vision to automatically extract bug information including title, severity, steps, expected/actual results, and store as JSON
---

# Spec: Bug Screenshot Recognition

## 1. Overview

**Project:** test_manager
**Type:** New Feature (Backend + Frontend)
**Scope:** Single goal - Add AI-powered screenshot bug recognition feature
**Token Estimate:** ~1200 tokens (within optimal range)

## 2. Functionality Specification

### 2.1 Core Features

#### Backend API: `/api/bug/recognize-screenshot`

**Input:**
- `image`: Image file (multipart/form-data)
- Supported formats: PNG, JPG, JPEG, GIF, BMP, WEBP

**Processing:**
1. Save uploaded image to `{DATA_DIR}/uploads/bugs/` directory
2. Use Baidu OCR + AI Vision API to analyze screenshot
3. Extract structured bug information:
   - **标题 (title)**: Bug title/description
   - **Bug等级 (severity)**: Critical / Major / Minor / Low (严重/一般/轻微/建议)
   - **操作步骤 (steps)**: Step-by-step reproduction steps
   - **预期结果 (expected_result)**: What should happen
   - **实际结果 (actual_result)**: What actually happened
   - **截图地址 (screenshot_path)**: Path to stored screenshot
   - **识别时间 (recognized_at)**: Timestamp of recognition
   - **原始文本 (raw_text)**: Raw OCR text for reference

**Output:**
```json
{
  "success": true,
  "data": {
    "title": "用户登录页面显示异常",
    "severity": "一般",
    "steps": "1. 打开浏览器\n2. 访问登录页面\n3. 输入用户名密码\n4. 点击登录按钮",
    "expected_result": "页面跳转到首页",
    "actual_result": "页面显示500错误",
    "screenshot_path": "/backend/data/uploads/bugs/uuid_filename.png",
    "recognized_at": "2026-03-30T12:00:00",
    "raw_text": "原始OCR识别文本..."
  }
}
```

**Error Handling:**
- Invalid image format → 400 with message
- Baidu API failure → 500 with fallback to basic OCR
- Image too large (>10MB) → 400 with size limit message

#### Backend API: `/api/bug/list`

**Purpose:** List all recognized bug records

**Output:**
```json
{
  "success": true,
  "data": {
    "total": 10,
    "bugs": [
      {
        "id": "uuid",
        "title": "...",
        "severity": "...",
        "steps": "...",
        "screenshot_path": "...",
        "recognized_at": "..."
      }
    ]
  }
}
```

#### Backend API: `/api/bug/delete/<id>`

**Purpose:** Delete a specific bug record

### 2.2 Frontend Integration

**New Tab/Section:** "截图识别" (Screenshot Recognition)

**UI Components:**
1. **Image Upload Area**
   - Drag & drop zone
   - File picker button
   - Preview of selected image

2. **Recognition Results Display**
   - Form with pre-filled fields from AI recognition
   - Editable fields: title, severity, steps, expected_result, actual_result
   - Screenshot thumbnail

3. **Action Buttons**
   - "识别" (Recognize) - trigger AI analysis
   - "保存" (Save) - save to JSON
   - "清空" (Clear) - reset form

4. **History List**
   - Table showing previously recognized bugs
   - View/Delete actions

### 2.3 Data Storage

**File:** `{DATA_DIR}/bugs_recognized.json`

**Structure:**
```json
{
  "bugs": [
    {
      "id": "uuid",
      "title": "...",
      "severity": "...",
      "steps": "...",
      "expected_result": "...",
      "actual_result": "...",
      "screenshot_path": "...",
      "recognized_at": "ISO8601 timestamp"
    }
  ],
  "total": 10,
  "last_updated": "ISO8601 timestamp"
}
```

### 2.4 Dependencies

**Required Python packages:**
- `baidu-aip` (Baidu AI SDK) - for OCR and image recognition
- Existing dependencies (Flask, etc.)

**Alternative fallback:**
- Basic PIL/Pytesseract if Baidu API unavailable

## 3. Acceptance Criteria

### AC1: Image Upload
- [ ] User can select image via file picker
- [ ] User can drag & drop image
- [ ] Image preview displays after selection
- [ ] Supported formats: PNG, JPG, JPEG, GIF, BMP, WEBP

### AC2: AI Recognition
- [ ] Clicking "识别" sends image to backend
- [ ] Backend calls Baidu AI API
- [ ] Response populates form fields within 5 seconds (typical)
- [ ] Graceful fallback if Baidu API fails

### AC3: Bug Record Saving
- [ ] Clicking "保存" writes bug record to JSON file
- [ ] Record includes all extracted fields
- [ ] Screenshot is saved to proper directory
- [ ] Duplicate entries are allowed (each has unique ID)

### AC4: History Management
- [ ] List shows all previously recognized bugs
- [ ] User can view details of past recognition
- [ ] User can delete a bug record

### AC5: Error Handling
- [ ] Invalid file type shows user-friendly error
- [ ] Network failure shows retry option
- [ ] Large file (>10MB) rejected with message

## 4. File Changes

### New Files:
- `backend/bug_screenshot_recognizer.py` - Baidu AI integration
- `backend/routes/bug_screenshot.py` - API routes (or add to server.py)

### Modified Files:
- `backend/server.py` - Add new routes
- `frontend/index.html` - Add screenshot recognition UI
- `requirements.txt` - Add baidu-aip dependency

### Configuration:
- Baidu API credentials (APP_ID, API_KEY, SECRET_KEY) - via environment variables or config
