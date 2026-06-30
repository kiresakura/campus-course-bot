# Privacy & Data Notice

> This document explains how the project handles data. The deployer (whoever self-hosts the bot)
> is the data controller and is responsible for complying with local laws (e.g. Taiwan's Personal
> Data Protection Act) and the data source's terms of service.

## 1. Data source

- Course-review data comes from **NCKUHUB**'s public course pages and is fetched by the deployer
  via `build_cache.py`.
- This open-source repository contains **no** scraped dataset; `data/course_cache.json` is
  `.gitignore`d.
- Course comments belong to their original authors / NCKUHUB. The bot only shows summaries on
  demand when a user queries them and **does not store commenter identities**.

## 2. What the bot reads

- The Discord adapter uses **slash commands only** and does **not** enable the privileged
  `message_content` intent, so it does not read ordinary chat messages.
- The bot does not actively collect or store user personal data; query parameters are used only to
  generate a reply in real time.

## 3. Instructor personal data & reputation (important)

- Course data may include **instructor names** mapped to subjective ratings. This constitutes
  processing of personal data about identifiable individuals.
- Features like "worst courses / low scores" present **other people's subjective opinions**, not
  facts. Do not use them for harassment, public shaming, or defamation.
- If you are an instructor and want related data removed from the bot, please reach out via the
  repo's contact channels; the deployer should comply.
- If you deploy publicly, we recommend:
  - Prominently labelling content as "subjective opinion, for reference only" (the project does
    this by default).
  - De-identifying instructor names or limiting "worst course"-style features where appropriate.
  - Providing an appeal / removal channel.

## 4. Third-party services

- AI / LLM features: the project currently contains **no** AI/LLM functionality (the former
  roleplay feature has been removed).
- Each chat platform (Discord / Telegram / LINE) handles messages under its own privacy policy.

## 5. Contact

For data-related requests or questions, use the repo's Issues (non-sensitive) or the Security
private reporting flow (sensitive).
