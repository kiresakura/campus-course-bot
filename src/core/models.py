"""核心資料模型與「中性回應模型」。

BotResponse 是平台無關的回應格式，由各 adapter 自行渲染成
Discord Embed / Telegram 訊息 / LINE Flex 等。core 內不得 import 任何平台 SDK。
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Optional


# ---------------------------------------------------------------------------
# 課程資料
# ---------------------------------------------------------------------------
@dataclass
class Course:
    id: str
    name: str
    dept: str
    teacher: str
    credits: int = 0
    time: str = ""
    classroom: str = ""
    sweet: float = 0.0      # 甜度
    cold: float = 0.0       # 涼度
    got: float = 0.0        # 收穫
    rate_count: int = 0     # 評分人數
    comments: Optional[List[Dict]] = None

    @classmethod
    def from_api_response(cls, data: dict) -> Optional["Course"]:
        """從 NCKUHUB 端點回應建立 Course 物件。"""
        if not data or "courseInfo" not in data:
            return None

        info = data["courseInfo"]
        return cls(
            id=str(info.get("id", "")),
            name=info.get("課程名稱", ""),
            dept=info.get("系所名稱", ""),
            teacher=info.get("老師", ""),
            credits=info.get("學分", 0) or 0,
            time=info.get("時間", ""),
            classroom=info.get("教室", ""),
            sweet=float(data.get("sweet", 0) or 0),
            cold=float(data.get("cold", 0) or 0),
            got=float(data.get("got", 0) or 0),
            rate_count=int(data.get("rate_count", 0) or 0),
            comments=data.get("comment", []),
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# 中性回應模型（平台無關）
# ---------------------------------------------------------------------------
class ResponseStyle(Enum):
    """語意化樣式；各 adapter 對應到自己的顏色/排版。"""

    PRIMARY = "primary"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    SWEET = "sweet"
    COLD = "cold"


@dataclass
class ResponseField:
    name: str
    value: str
    inline: bool = False


@dataclass
class BotResponse:
    """一則平台無關的回應。"""

    title: str
    description: str = ""
    fields: List[ResponseField] = field(default_factory=list)
    footer: str = ""
    style: ResponseStyle = ResponseStyle.PRIMARY

    def add_field(self, name: str, value: str, inline: bool = False) -> "BotResponse":
        self.fields.append(ResponseField(name=name, value=value, inline=inline))
        return self

    def to_markdown(self) -> str:
        """渲染成純文字/Markdown，供 Telegram / LINE / CLI 等使用。"""
        lines: List[str] = []
        if self.title:
            lines.append(f"**{self.title}**")
        if self.description:
            lines.append(self.description)
        for f in self.fields:
            lines.append("")
            lines.append(f"**{f.name}**")
            if f.value:
                lines.append(f.value)
        if self.footer:
            lines.append("")
            lines.append(f"_{self.footer}_")
        return "\n".join(lines).strip()
