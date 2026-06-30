# campus-course-bot - Technical Specification

> ⚠️ Unofficial project, not affiliated with NCKUHUB or National Cheng Kung University (NCKU).
> This document is an **early design record**. Parts of it are now outdated after refactoring
> (the public API server was removed; the project moved to a multi-platform adapter architecture).
> For the current architecture, see [README.md](README.md).

## 1. Overview

### 1.1 Goal
Build a course-review query bot (multi-platform: Discord / Telegram / LINE) to help students make
course-selection decisions.

### 1.2 Key finding
NCKUHUB's course pages return JSON (an **undocumented, unofficial endpoint** — check its terms of
service before use):
```
GET https://nckuhub.com/course/{course_id}
```

Response shape (Chinese keys are the actual API field names):
```json
{
  "got": "8.0",           // takeaway (1-10)
  "cold": "7.0",          // easiness (1-10)
  "sweet": "9.0",         // sweetness / grade generosity (1-10)
  "rate_count": 5,        // number of ratings
  "courseInfo": {
    "id": "1234",
    "系所名稱": "歷史系 HIST",
    "課程名稱": "中國通史",
    "老師": "王大明",
    "學分": 3,
    "時間": "[1]2~4",
    "教室": "文學院 101",
    "comment_num": 3
  },
  "comment": [
    {
      "comment": "...",
      "semester": "113-1"
    }
  ],
  "rates": [...]
}
```

---

## 2. Functional spec

### 2.1 Commands
(Discord command names are in Chinese; Telegram uses English aliases — see README.)

| Command | Args | Description |
|---------|------|-------------|
| `/課程 <keyword>` | keyword: str | Search courses; show ratings and a comment summary |
| `/教授 <name>` | name: str | Average ratings across a professor's courses |
| `/甜課 [dept]` | dept: str (optional) | Recommend high-sweetness courses |
| `/涼課 [dept]` | dept: str (optional) | Recommend high-easiness courses |
| `/比較 <A> <B>` | a: str, b: str | Head-to-head rating comparison |
| `/雷課 [n]` | limit: int = 5 | Show low-scoring courses (reference only) |
| `/詳細 <course_id>` | course_id: int | Show full comments |

### 2.2 Display format (example)

Course card example:
```
┌─────────────────────────────────┐
│ 📚 中國通史                      │
│ 歷史系 HIST ｜ 王大明            │
├─────────────────────────────────┤
│ 🍬 sweet:    8.5/10  ████████░░ │
│ 🛋️ easy:     7.0/10  ███████░░░ │
│ 📖 takeaway: 9.0/10  █████████░ │
│ 👥 ratings: 12                  │
└─────────────────────────────────┘
```

---

## 3. Architecture (historical — see README for the current core/adapters design)

### 3.1 Data cache strategy

NCKUHUB has no bulk API, so a local cache is built:

1. **Initial build**: scan course IDs 1–15000 and store to `data/course_cache.json`.
2. **Incremental update**: refresh periodically, fetching only changed courses.
3. **Cache structure**:
```json
{
  "last_updated": "2024-12-01T00:00:00Z",
  "courses": {
    "1234": {
      "id": "1234", "name": "...", "dept": "...", "teacher": "...",
      "sweet": 8.5, "cold": 7.0, "got": 9.0, "rate_count": 12
    }
  },
  "by_teacher": { "...": ["1234", "5678"] },
  "by_dept":    { "...": ["1234", "2345"] }
}
```

### 3.2 Search
Simple fuzzy matching (exact-substring first, then optional fuzzy via `thefuzz`). See
`src/core/cache.py` for the current implementation.

---

## 4. Configuration

See `.env.example` for the current variables (`BOT_PLATFORM`, `DISCORD_TOKEN`, `GUILD_ID`,
`TELEGRAM_BOT_TOKEN`, `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`, `LOG_LEVEL`) and
`requirements.txt` for pinned dependencies.

---

## 5. Deployment options

| Option | Cost | Difficulty | Notes |
|--------|------|-----------|-------|
| Local | Free | ⭐ | Development / testing |
| Railway | Free tier | ⭐⭐ | Recommended for small deployments |
| Fly.io | Free tier | ⭐⭐ | Alternative |
| Your own VPS | from ~$5/mo | ⭐⭐⭐ | Long-term, stable hosting |

---

## 6. Notes

1. **Rate limiting**: NCKUHUB has no explicit rate limit, but space requests out (~0.5 s each).
2. **Cache refresh**: course data changes heavily at the start of a semester; refresh more often then.
3. **Privacy**: do not store or display commenter identities.
4. **Error handling**: the endpoint may return empty data or 404 — handle both gracefully.
