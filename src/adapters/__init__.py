"""聊天平台 adapter：把平台無關的 core 接到 Discord / Telegram / LINE 等。

每個 adapter 只在自己的 start() 內 lazy import 平台 SDK，
因此「import 這個模組」不會強制要求安裝對應 SDK。
"""
