"""SQLAlchemy ORM models.

All models inherit from app.db.Base. Importing this package registers every
model on the declarative metadata so Alembic autogenerate and the lifespan
seeder can see them.
"""

from app.models.daily_log import DailyLog
from app.models.phase import Phase
from app.models.recap import Recap
from app.models.session import Session
from app.models.settings import AppSettings
from app.models.user import User
from app.models.week import Week

__all__ = [
    "Phase",
    "Week",
    "User",
    "AppSettings",
    "Session",
    "DailyLog",
    "Recap",
]