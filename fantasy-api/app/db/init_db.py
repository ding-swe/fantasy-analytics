from app.db.base import Base
from app.db.database import get_engine
from app.db import models  # noqa: F401 - registers model tables on Base.metadata


def main() -> None:
    Base.metadata.create_all(bind=get_engine())
    print("Database tables are ready.")


if __name__ == "__main__":
    main()
