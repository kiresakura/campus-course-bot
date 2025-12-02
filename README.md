# NCKUHUB Discord Bot 🎓

> 一個可以即時查詢 NCKUHUB 課程評價的 Discord Bot，讓你在選課時不再踩雷！

## ✨ 功能特色

- 🔍 **課程搜尋** - 用關鍵字搜尋課程，顯示甜度/涼度/收穫評分
- 👨‍🏫 **教授查詢** - 查看特定教授的所有課程評價
- 🍬 **甜課推薦** - 找出高甜度的輕鬆拿分課程
- 🛋️ **涼課推薦** - 找出最涼的課程讓你躺著修
- ⚔️ **課程 PK** - 兩門課直接比較，選課不再猶豫
- ⚠️ **雷課警報** - 公開低分課程，避免踩雷

## 🚀 快速開始

```bash
# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入你的 Discord Bot Token

# 啟動 Bot
python src/bot.py
```

## 📁 專案結構

```
NCKUHUB-Discord-Bot/
├── src/
│   ├── bot.py              # Bot 主程式 & 事件處理
│   ├── nckuhub_api.py      # NCKUHUB API 封裝
│   ├── commands.py         # Slash Commands 定義
│   └── embeds.py           # Discord Embed 美化模組
├── data/
│   └── course_cache.json   # 課程資料快取
├── logs/
│   └── bot.log             # 運行日誌
├── .env.example            # 環境變數範本
├── requirements.txt        # Python 依賴
├── SPEC.md                 # 詳細規格書
└── README.md               # 本文件
```

## 🔧 技術棧

- Python 3.10+
- discord.py 2.x (Slash Commands)
- aiohttp (非同步 HTTP 請求)
- NCKUHUB 公開 API

## 📜 License

MIT License - 隨便用，但記得請我喝飲料 ☕

---

Made with ♡ by 成大歷史系の技術宅
