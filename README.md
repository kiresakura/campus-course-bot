# campus-course-bot 🎓

> 一個多平台的課程評價查詢機器人 —— 用關鍵字查甜度／涼度／收穫，選課不再踩雷。
> A multi-platform course-review query bot (Discord / Telegram / LINE).

---

## ⚠️ 免責聲明 / Disclaimer

**本專案為非官方（unofficial）作品，與 NCKUHUB 平台及國立成功大學（NCKU）無任何隸屬、合作或背書關係。**
This is an **unofficial** project and is **not affiliated with, endorsed by, or connected to** the NCKUHUB platform or National Cheng Kung University (NCKU).

- 課程資料來源為 NCKUHUB 的公開課程頁面；本專案**不內附、不散布**任何抓取的資料集，使用者須自行於本機建立快取（見下方）。
- 評分（甜度／涼度／收穫）與「雷課」皆為**他人主觀評價**，僅供參考，不代表事實，亦不構成對任何教師或課程的評斷。
- 使用前請自行確認符合資料來源的服務條款與當地法律（個資、著作權、名譽等）。詳見 [PRIVACY.md](PRIVACY.md)。

---

## ✨ 功能特色

- 🔍 **課程搜尋** — 關鍵字搜尋課程，顯示甜度／涼度／收穫
- 👨‍🏫 **教授查詢** — 查看某教授的所有課程平均評價
- 🍬 **甜課 / 🛋️ 涼課推薦** — 高甜度／高涼度排行
- ⚔️ **課程 PK** — 兩門課直接比較
- ⚠️ **雷課警報** — 低分課程提醒（主觀、僅供參考）
- 💬 **課程詳細** — 即時查看課程心得

## 🧩 架構：一套核心，多平台接入

```
src/
├── core/                  # 平台無關的核心（不依賴任何聊天平台 SDK）
│   ├── models.py          #   Course + 中性回應模型 BotResponse
│   ├── cache.py           #   本地快取與查詢（thefuzz 為選用）
│   ├── nckuhub_client.py  #   資料抓取（User-Agent + 退避）
│   └── course_service.py  #   所有指令邏輯 → 回傳 BotResponse
├── adapters/              # 各平台 adapter（SDK 皆 lazy import）
│   ├── base.py            #   BotAdapter 介面
│   ├── discord_adapter.py #   ✅ Discord（已實作）
│   ├── telegram_adapter.py#   🧪 Telegram（骨架，可運作）
│   └── line_adapter.py    #   🧪 LINE（骨架 + Webhook 待補）
└── run.py                 # 進入點，依 BOT_PLATFORM 選擇平台
```

新增一個平台 = 繼承 `BotAdapter`，實作 `render(BotResponse)` 與 `start()`，核心邏輯完全重用。

| 平台 | 狀態 | 需要的 SDK |
|------|------|-----------|
| Discord | ✅ 已實作 | `discord.py`（預設安裝） |
| Telegram | 🧪 可運作骨架 | `pip install python-telegram-bot==21.4` |
| LINE | 🧪 骨架（需自建 Webhook） | `pip install line-bot-sdk==3.11.0` |

## 🚀 快速開始

```bash
# 1) 安裝依賴
pip install -r requirements.txt

# 2) 設定環境變數
cp .env.example .env
#    編輯 .env：選擇 BOT_PLATFORM，填入對應平台的 Token

# 3) 建立你自己的課程快取（見下方說明，必要步驟）
python build_cache.py

# 4) 啟動（預設 Discord；或用 BOT_PLATFORM=telegram / line）
python src/run.py
```

## 🗃️ 建立你自己的快取（重要）

本專案**不附帶**課程資料集。請自行執行 `python build_cache.py` 在本機產生
`data/course_cache.json`（已列入 `.gitignore`，不會被 commit）。

> 抓取時請尊重資料來源：`core/nckuhub_client.py` 已內建可識別的 User-Agent、
> 並發限制與請求退避。請勿移除這些禮貌性設定，亦**請勿再次散布**抓取到的資料。

## 🔧 技術棧

- Python 3.10+
- discord.py 2.x（預設 adapter）
- aiohttp（非同步 HTTP）
- thefuzz（選用，模糊搜尋；缺少時自動退化為精確比對）

## 🔒 安全與隱私

- 漏洞通報：見 [SECURITY.md](SECURITY.md)
- 隱私說明（資料來源、機器人讀取範圍）：見 [PRIVACY.md](PRIVACY.md)

## 📜 License

[MIT License](LICENSE) © 2026 Crimson
