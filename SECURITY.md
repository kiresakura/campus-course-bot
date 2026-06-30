# Security Policy

## 回報漏洞 / Reporting a Vulnerability

如果你發現安全性問題，請**不要**開公開 issue。請改用：

- GitHub「Security」分頁 → **Report a vulnerability**（私密回報），或
- 透過 repo 擁有者的 GitHub 個人頁所列聯絡方式私訊。

請盡量提供：重現步驟、影響範圍、可能的修補建議。我們會在合理時間內回覆並協調修補與揭露。

If you find a security issue, please **do not** open a public issue. Use GitHub's
private "Report a vulnerability" flow instead, with reproduction steps and impact.

## 部署者請注意 / Hardening notes for self-hosters

本機器人預設只啟用聊天平台所需的最小權限，但你自行部署時仍須留意：

- **權杖保密**：`.env` 已被 `.gitignore` 排除，切勿 commit 任何 Token / 金鑰。
- **最小權限**：Discord adapter 不啟用 `message_content` 特權 intent（只用 Slash Command）。
- **資料抓取**：`build_cache.py` 會對第三方網站發出大量請求；請保留內建的 User-Agent、
  並發限制與退避，並遵守對方服務條款。請勿將抓取到的 `data/course_cache.json` 散布。
- **不要新增無認證的對外管理端點**（本專案已移除先前的 REST API server 與其
  `/cache/rebuild` 端點，以避免被當成攻擊跳板）。
- **輸入處理**：所有對外回覆皆不直接夾帶原始例外訊息（避免資訊外洩）。

## 支援範圍

僅維護 `main` 分支的最新版本。
