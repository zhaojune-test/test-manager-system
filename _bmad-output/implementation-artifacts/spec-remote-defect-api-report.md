---
status: completed
version: 1.0.0
date: 2026-03-30
title: Remote Defect API Report Generation - Generate test reports from remote defect API
description: Fetch defect data from remote API with version filtering and token authentication, then generate test reports
baseline_commit: NO_VCS
---

# Spec: Remote Defect API Report Generation

## 1. Overview

**Project:** test_manager
**Type:** New Feature (Backend API + Frontend Enhancement)
**Scope:** Single goal - Integrate with remote defect API to generate test reports
**Token Estimate:** ~1400 tokens (within optimal range)

## 2. Functionality Specification

### 2.1 Core Features

#### Remote API Integration

**API Endpoint:** `POST https://edsp.cosmoplat.comproject/defect/list/page`

**Request:**
```json
{
  "projectId": "2007642735088656025",
  "version": "2038456792337300195",
  "page": 1,
  "size": 1000
}
```

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Response Field Mapping:**
| Remote Field | Local Field | Description |
|-------------|-------------|-------------|
| id | id | 缺陷ID |
| title | title | 缺陷标题 |
| defectType | category | 缺陷分类 |
| severityDegree | severity | 严重程度 (1=致命, 2=严重, 3=一般, 4=轻微) |
| status | status | 状态 (0=待处理, 1=处理中, 2=已修复, 3=暂不修复, 4=已关闭, 5=再次打开) |
| handleName | handler | 处理人 |
| verifierName | verifier | 验证人 |
| createdAt | create_time | 创建时间 |
| closeDate | close_time | 关闭时间 |
| description | reason | 从HTML中解析的操作步骤、预期结果、实际结果 |
| rpName | pm | 产品经理 |
| versionName | version | 版本名称 |

**Status Mapping:**
```python
STATUS_MAP = {
    0: '待处理',
    1: '处理中',
    2: '已修复',
    3: '暂不修复',
    4: '已关闭',
    5: '再次打开'
}
```

**Severity Mapping:**
```python
SEVERITY_MAP = {
    1: '致命',
    2: '严重',
    3: '一般',
    4: '轻微'
}
```

#### Description HTML Parsing

Extract structured data from HTML description field:
- `[操作步骤]` section → steps
- `[实际结果]` section → actual_result
- `[预期结果]` section → expected_result

#### Configuration

**Environment Variables:**
- `EDSP_API_URL` - API base URL (default: https://edsp.cosmoplat.com)
- `EDSP_PROJECT_ID` - Project ID for defect list
- `EDSP_API_TOKEN` - Bearer token for authentication

### 2.2 Backend API Changes

#### New API: `/api/bug-report/fetch-remote`

**Purpose:** Fetch defect list from remote API with version filtering

**Request Body:**
```json
{
  "version": "版本ID或版本名称",
  "page": 1,
  "size": 1000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 50,
    "defects": [...],
    "versions": [{"id": "...", "name": "版本1"}, ...]
  }
}
```

#### Modified API: `/api/bug-report/generate`

**Changes:**
- Accept optional `source` parameter: "local" (default) or "remote"
- If source=remote, fetch from remote API instead of local Excel

### 2.3 Frontend Changes

**New UI Elements:**
1. **Source Selection**
   - Radio buttons: "本地Excel" / "远程API"

2. **Remote Source Form** (shown when remote selected)
   - Version dropdown (populated from API)
   - Token input field (optional, for custom token)
   - "获取数据" button

3. **Data Preview**
   - Show fetched defect count
   - Show statistics (by severity, by status)

### 2.4 Data Storage

**Cache:** `{DATA_DIR}/remote_defects_cache.json`
- Cache fetched data to reduce API calls
- Include cache timestamp
- Expire after 1 hour

### 2.5 Error Handling

- Invalid token → 401 with "认证失败，请检查Token"
- Network error → 502 with "无法连接到远程服务器"
- No data for version → 404 with "该版本暂无缺陷数据"
- Parse error → 500 with error details

## 3. Acceptance Criteria

### AC1: Remote API Integration
- [ ] Can fetch defects from remote API with valid token
- [ ] Can filter defects by version
- [ ] Token authentication works correctly
- [ ] Handles 401/502 errors gracefully

### AC2: Data Parsing
- [ ] Correctly maps remote fields to local fields
- [ ] Parses HTML description to extract steps/expected/actual
- [ ] Handles missing/null fields gracefully

### AC3: Report Generation
- [ ] Generates report from remote data
- [ ] Report includes all required sections
- [ ] Statistics are accurate

### AC4: Frontend Integration
- [ ] Can switch between local/remote source
- [ ] Version dropdown populated from API
- [ ] Shows loading state during fetch
- [ ] Shows error messages on failure

### AC5: Configuration
- [ ] Token configurable via UI (session) or environment variable
- [ ] Project ID configurable
- [ ] Version list fetched dynamically

## 4. File Changes

### New Files:
- `backend/remote_defect_client.py` - Remote API client with HTML parsing

### Modified Files:
- `backend/server.py` - Add `/api/bug-report/fetch-remote` endpoint
- `backend/bug_report_generator.py` - Support remote data source
- `frontend/index.html` - Add remote source UI elements

### Configuration:
- Environment variables for EDSP_API_URL, EDSP_PROJECT_ID, EDSP_API_TOKEN
