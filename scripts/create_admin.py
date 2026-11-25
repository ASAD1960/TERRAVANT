"""Create (or promote) an administrator.  Usage: python scripts/create_admin.py EMAIL "Full Name"
Password is read from the ADMIN_PASSWORD env var or prompted (never passed on the command line)."""
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Role, User  # noqa: E402
from app.services.seed import seed_reference_data  # noqa: E402


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    email, name = sys.argv[1].lower(), sys.argv[2]
    pw = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Admin password (min 10 chars): ")
    if len(pw) < 10:
        raise SystemExit("Password too short")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_reference_data(db)
        role = db.scalar(select(Role).where(Role.name == "admin"))
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.roles = [role]
        else:
            db.add(User(full_name=name, email=email, password_hash=hash_password(pw), roles=[role]))
        db.commit()
    print(f"Administrator ready: {email}")


if __name__ == "__main__":
    main()
