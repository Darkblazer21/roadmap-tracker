"""SQLAlchemy ORM models.

All models inherit from app.db.Base. Importing this package (via
``from app.models import ...``) registers every model on the declarative
metadata so Alembic autogenerate and the lifespan seeder can see them.
"""

from app.models.phase import Phase
from app.models.week import Week

__all__ = ["Phase", "Week"]