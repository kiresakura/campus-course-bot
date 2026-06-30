# Security Policy

## Reporting a vulnerability

If you find a security issue, please **do not** open a public issue. Instead:

- Use the GitHub **Security** tab → **Report a vulnerability** (private disclosure), or
- Contact the repo owner privately via the contact details on their GitHub profile.

Please include reproduction steps, impact, and any suggested fix. We will respond within a
reasonable time and coordinate the fix and disclosure.

## Hardening notes for self-hosters

The bot enables only the minimum permissions each chat platform needs, but when you self-host,
keep the following in mind:

- **Keep tokens secret.** `.env` is `.gitignore`d — never commit any token or key.
- **Least privilege.** The Discord adapter does not enable the privileged `message_content`
  intent (it uses slash commands only).
- **Data scraping.** `build_cache.py` issues many requests to a third-party site; keep the
  built-in User-Agent, concurrency limit, and backoff, and respect that site's terms of service.
  Do not redistribute the scraped `data/course_cache.json`.
- **No unauthenticated admin endpoints.** This project removed the previous REST API server and
  its `/cache/rebuild` endpoint to avoid being used as an attack amplifier.
- **Input handling.** User-facing replies never include raw exception text (to avoid information
  leakage); details are logged server-side only.
- **LINE webhook.** The LINE adapter verifies the `X-Line-Signature` HMAC on every request and
  rejects unsigned ones; always expose it over HTTPS.

## Supported versions

Only the latest version on the `main` branch is maintained.
