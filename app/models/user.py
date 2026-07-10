"""User model - single seeded user for the local tracker.

The lifespan creates this user on first boot from SEED_USERNAME / SEED_PASSWORD
env vars. Login returns a JWT; write routes require it.
"""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"