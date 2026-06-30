"""Core data models and the neutral response model.

BotResponse is a platform-agnostic response that each adapter renders into a
Discord Embed / Telegram message / LINE message, etc. The core must not import
any chat-platform SDK.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Optional


# ---------------------------------------------------------------------------
# Course data
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
    sweet: float = 0.0      # sweetness
    cold: float = 0.0       # easiness
    got: float = 0.0        # takeaway
    rate_count: int = 0     # number of ratings
    comments: Optional[List[Dict]] = None

    @classmethod
    def from_api_response(cls, data: dict) -> Optional["Course"]:
        """Build a Course from an NCKUHUB endpoint response."""
        if not data or "courseInfo" not in data:
            return None

        info = data["courseInfo"]
        # NOTE: the Chinese keys below are the actual NCKUHUB API field names.
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
# Neutral response model (platform-agnostic)
# ---------------------------------------------------------------------------
class ResponseStyle(Enum):
    """Semantic style; each adapter maps it to its own color/layout."""

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
    """A single platform-agnostic response."""

    title: str
    description: str = ""
    fields: List[ResponseField] = field(default_factory=list)
    footer: str = ""
    style: ResponseStyle = ResponseStyle.PRIMARY

    def add_field(self, name: str, value: str, inline: bool = False) -> "BotResponse":
        self.fields.append(ResponseField(name=name, value=value, inline=inline))
        return self

    def to_markdown(self) -> str:
        """Render to plain text / Markdown for Telegram / LINE / CLI, etc."""
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
