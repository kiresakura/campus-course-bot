"""Chat-platform adapters: connect the platform-agnostic core to Discord / Telegram / LINE.

Each adapter lazy-imports its platform SDK inside start(), so importing this module
never hard-requires the corresponding SDK.
"""
