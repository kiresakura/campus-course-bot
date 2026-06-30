# campus-course-bot 🎓

[![CI](https://github.com/kiresakura/campus-course-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/kiresakura/campus-course-bot/actions/workflows/ci.yml)

> A multi-platform course-review query bot (Discord / Telegram / LINE) — search by
> keyword and see "sweetness / easiness / takeaway" ratings to pick courses with confidence.

---

## ⚠️ Disclaimer

**This is an unofficial project and is not affiliated with, endorsed by, or connected to the
NCKUHUB platform or National Cheng Kung University (NCKU).**
本專案為非官方作品,與 NCKUHUB 平台及國立成功大學(NCKU)無任何隸屬、合作或背書關係。

- Course data comes from NCKUHUB's public course pages. This project does **not** bundle or
  redistribute any scraped dataset — you build your own local cache (see below).
- Ratings (sweetness / easiness / takeaway) and "worst courses" are **other people's subjective
  opinions**, provided for reference only. They are not facts and are not a judgement of any
  instructor or course.
- Before deploying, make sure you comply with the data source's terms of service and your local
  laws (personal data, copyright, defamation, etc.). See [PRIVACY.md](PRIVACY.md).

---

## ✨ Features

- 🔍 **Course search** — search by keyword; shows sweetness / easiness / takeaway
- 👨‍🏫 **Professor lookup** — average ratings across a professor's courses
- 🍬 **Sweet / 🛋️ Easy rankings** — top courses by sweetness / easiness
- ⚔️ **Course compare** — head-to-head comparison of two courses
- ⚠️ **Worst-course alert** — low-rated courses (subjective, reference only)
- 💬 **Course detail** — live fetch of course comments

## 🧩 Architecture: one core, many platforms

```
src/
├── core/                  # Platform-agnostic core (no chat-platform SDK)
│   ├── models.py          #   Course + neutral response model (BotResponse)
│   ├── cache.py           #   Local cache & queries (thefuzz optional)
│   ├── nckuhub_client.py  #   Data fetching (User-Agent + backoff)
│   └── course_service.py  #   All command logic → returns BotResponse
├── adapters/              # Per-platform adapters (SDKs lazy-imported)
│   ├── base.py            #   BotAdapter interface
│   ├── discord_adapter.py #   ✅ Discord
│   ├── telegram_adapter.py#   ✅ Telegram
│   └── line_adapter.py    #   ✅ LINE
└── run.py                 # Entrypoint; picks a platform via BOT_PLATFORM
```

Adding a platform = subclass `BotAdapter` and implement `render(BotResponse)` and `start()`;
all the core logic is reused.

| Platform | Status | Transport | SDK |
|----------|--------|-----------|-----|
| Discord  | ✅ Implemented | Slash commands | `discord.py` (installed by default) |
| Telegram | ✅ Implemented | Polling | `pip install python-telegram-bot==21.4` |
| LINE     | ✅ Implemented | Webhook (needs public HTTPS) | None (uses built-in aiohttp) |

## 🚀 Quick start

```bash
# 1) Install dependencies
pip install -r requirements.txt

# 2) Configure environment
cp .env.example .env
#    Edit .env: pick BOT_PLATFORM and fill in that platform's token

# 3) Build your own course cache (required — see below)
python build_cache.py

# 4) Run (defaults to Discord; or BOT_PLATFORM=telegram / line)
python src/run.py
```

## 🛰️ Per-platform setup

Switch platforms with the `BOT_PLATFORM` environment variable (`discord` / `telegram` / `line`).

**Discord** (slash commands)
```bash
BOT_PLATFORM=discord DISCORD_TOKEN=xxx python src/run.py
```
After inviting the bot to a server, use the slash commands `/課程 /教授 /甜課 /涼課 /比較 /雷課 /詳細`
(search / professor / sweet / easy / compare / worst / detail). Command names are in Chinese
because the bot serves a Chinese-speaking campus audience.

**Telegram** (polling)
```bash
pip install python-telegram-bot==21.4
BOT_PLATFORM=telegram TELEGRAM_BOT_TOKEN=xxx python src/run.py
```
Get a token from [@BotFather](https://t.me/BotFather). Commands use English aliases:
`/search /professor /sweet /cold /compare /worst /detail` (`/help` for usage).

**LINE** (webhook, HTTPS required)
```bash
BOT_PLATFORM=line LINE_CHANNEL_ACCESS_TOKEN=xxx LINE_CHANNEL_SECRET=yyy PORT=8000 python src/run.py
```
This starts a `/callback` endpoint on `PORT` with `X-Line-Signature` HMAC verification (unsigned
requests are rejected). Expose it over HTTPS (a reverse proxy or a platform such as Railway) and
set the Webhook URL in the LINE Developers Console to `https://your-domain/callback`. Users send
messages like `課程 微積分` or `詳細 1234`.

## 🗃️ Build your own cache (important)

This project does **not** ship a course dataset. Run `python build_cache.py` to generate
`data/course_cache.json` locally (it is `.gitignore`d and never committed).

> Please be respectful to the data source: `core/nckuhub_client.py` already sets an identifying
> User-Agent, limits concurrency, and backs off between requests. Do not remove these courtesy
> measures, and **do not redistribute** the scraped data.

## 🔧 Tech stack

- Python 3.10+
- discord.py 2.x (default adapter)
- aiohttp (async HTTP; also powers the LINE webhook server)
- thefuzz (optional fuzzy search; falls back to exact matching when absent)

## 🔒 Security & privacy

- Vulnerability reporting: see [SECURITY.md](SECURITY.md)
- Privacy notes (data provenance, what the bot reads): see [PRIVACY.md](PRIVACY.md)

## 📜 License

[MIT License](LICENSE) © 2026 Crimson
