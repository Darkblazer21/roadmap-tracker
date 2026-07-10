"""Pydantic v2 request/response schemas."""

from app.schemas.auth import LoginRequest, TokenOut, UserOut
from app.schemas.phase import PhaseOut, PhaseWithWeeks
from app.schemas.session import SessionCreate, SessionOut, WeekAggregate
from app.schemas.settings import SettingsOut, SettingsPatch
from app.schemas.week import WeekOut, WeekPatch

__all__ = [
    "LoginRequest",
    "TokenOut",
    "UserOut",
    "PhaseOut",
    "PhaseWithWeeks",
    "WeekOut",
    "WeekPatch",
    "SettingsOut",
    "SettingsPatch",
    "SessionCreate",
    "SessionOut",
    "WeekAggregate",
]