# campus-course-bot - 技術規格書

> ⚠️ 非官方專案，與 NCKUHUB 及成功大學（NCKU）無任何隸屬關係。本文件為早期設計紀錄，
> 部分內容已隨重構調整（已移除對外 API server、改為多平台 adapter 架構）。

## 1. 專案概述

### 1.1 目標
建立一個課程評價查詢機器人（多平台：Discord／Telegram／LINE），幫助學生選課決策。

### 1.2 核心發現
NCKUHUB 的課程頁面會回傳 JSON（**非官方文件化的端點**，使用前請確認其服務條款）：
```
GET https://nckuhub.com/course/{課程ID}
```

回傳格式：
```json
{
  "got": "8.0",           // 課堂收穫 (1-10)
  "cold": "7.0",          // 上課涼度 (1-10)
  "sweet": "9.0",         // 分數甜度 (1-10)
  "rate_count": 5,        // 評分人數
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
      "comment": "老師上課很有趣...",
      "semester": "113-1"
    }
  ],
  "rates": [...]
}
```

---

## 2. 功能規格

### 2.1 Slash Commands

| 指令 | 參數 | 說明 |
|------|------|------|
| `/課程 <關鍵字>` | keyword: str | 搜尋課程名稱，顯示評分與心得摘要 |
| `/教授 <姓名>` | name: str | 查詢該教授所有課程的平均評分 |
| `/甜課 [系所]` | dept: str (optional) | 推薦高甜度課程 (sweet >= 8) |
| `/涼課 [系所]` | dept: str (optional) | 推薦高涼度課程 (cold >= 8) |
| `/比較 <課程A> <課程B>` | a: str, b: str | 兩門課評分 PK |
| `/雷課 [數量]` | limit: int = 5 | 顯示低分課程警告 |
| `/詳細 <課程ID>` | course_id: int | 顯示完整心得內容 |

### 2.2 顯示格式 (Discord Embed)

課程卡片範例：
```
┌─────────────────────────────────┐
│ 📚 中國通史                      │
│ 歷史系 HIST ｜ 王大明            │
├─────────────────────────────────┤
│ 🍬 甜度: 8.5/10  ████████░░     │
│ 🛋️ 涼度: 7.0/10  ███████░░░     │
│ 📖 收穫: 9.0/10  █████████░     │
│ 👥 評分人數: 12                  │
├─────────────────────────────────┤
│ 💬 最新心得:                     │
│ 「老師上課很有趣，考試不難...」   │
│                    — 113-1 學生  │
└─────────────────────────────────┘
```

---

## 3. 技術架構

### 3.1 模組設計

```
src/
├── bot.py           # Discord Bot 初始化 & 事件監聽
│   - on_ready()
│   - on_error()
│   - 載入 commands cog
│
├── nckuhub_api.py   # NCKUHUB API 封裝
│   - class NCKUHubAPI:
│       - search_course(keyword) -> List[Course]
│       - get_course(id) -> Course
│       - get_professor_courses(name) -> List[Course]
│       - get_top_sweet(n, dept?) -> List[Course]
│       - get_top_cold(n, dept?) -> List[Course]
│       - get_worst_courses(n) -> List[Course]
│
├── commands.py      # Slash Commands 定義
│   - class CourseCommands(commands.Cog):
│       - /課程, /教授, /甜課, /涼課, /比較, /雷課, /詳細
│
└── embeds.py        # Embed 生成器
    - create_course_embed(course) -> Embed
    - create_comparison_embed(a, b) -> Embed
    - create_ranking_embed(courses, title) -> Embed
```

### 3.2 資料快取策略

由於 NCKUHUB 沒有批量 API，需要建立本地快取：

1. **初次建立**: 掃描課程 ID 1~15000，儲存到 `data/course_cache.json`
2. **增量更新**: 每週更新一次，只抓取有變動的課程
3. **快取結構**:
```json
{
  "last_updated": "2024-12-01T00:00:00Z",
  "courses": {
    "1234": {
      "id": "1234",
      "name": "中國通史",
      "dept": "歷史系",
      "teacher": "王大明",
      "sweet": 8.5,
      "cold": 7.0,
      "got": 9.0,
      "rate_count": 12
    }
  },
  "by_teacher": {
    "王大明": ["1234", "5678"]
  },
  "by_dept": {
    "歷史系": ["1234", "2345"]
  }
}
```

### 3.3 搜尋實作

使用簡單的模糊匹配（不需要額外套件）：
```python
def search_course(keyword: str) -> List[Course]:
    keyword = keyword.lower()
    results = []
    for course in cache.values():
        if keyword in course['name'].lower() or \
           keyword in course['teacher'].lower():
            results.append(course)
    return sorted(results, key=lambda x: x['rate_count'], reverse=True)[:10]
```

---

## 4. 環境設定

### 4.1 .env.example
```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_test_server_id  # 開發時用，正式部署可移除
LOG_LEVEL=INFO
```

### 4.2 requirements.txt
```
discord.py>=2.3.0
aiohttp>=3.8.0
python-dotenv>=1.0.0
```

---

## 5. 開發步驟

### Phase 1: 基礎建設
1. [ ] 設定 Discord Bot 並取得 Token
2. [ ] 實作 bot.py 基本框架
3. [ ] 實作 nckuhub_api.py 單一課程查詢

### Phase 2: 快取系統
4. [ ] 實作課程 ID 掃描器（背景執行）
5. [ ] 建立 course_cache.json 結構
6. [ ] 實作搜尋功能

### Phase 3: 指令實作
7. [ ] /課程 指令
8. [ ] /教授 指令
9. [ ] /甜課 /涼課 指令
10. [ ] /比較 指令
11. [ ] /雷課 指令

### Phase 4: 美化 & 優化
12. [ ] Discord Embed 美化
13. [ ] 錯誤處理 & 日誌
14. [ ] Rate limiting（避免被 NCKUHUB 擋）

---

## 6. 部署選項

| 方案 | 成本 | 難度 | 建議 |
|------|------|------|------|
| 本機執行 | 免費 | ⭐ | 開發測試用 |
| Railway | 免費額度 | ⭐⭐ | 小型部署推薦 |
| Fly.io | 免費額度 | ⭐⭐ | 備選方案 |
| 自己的 VPS | $5/月起 | ⭐⭐⭐ | 長期穩定運行 |

---

## 7. 注意事項

1. **Rate Limiting**: NCKUHUB 沒有明確的 rate limit，但建議每次請求間隔 0.5 秒
2. **快取更新**: 學期初課程資料會大量變動，建議加開更新頻率
3. **隱私**: 不要儲存或顯示評論者身份
4. **錯誤處理**: API 可能回傳空資料或 404，需妥善處理
