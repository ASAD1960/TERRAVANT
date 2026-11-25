"""Seed a demo farmer with a farm/field so the UI is not empty. Dev only."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Farm, Field, Role, SoilRecord, User  # noqa: E402
from app.services.seed import seed_reference_data  # noqa: E402

if get_settings().is_prod:
    raise SystemExit("Refusing to seed demo data in production")
Base.metadata.create_all(engine)
with SessionLocal() as db:
    seed_reference_data(db)
    if not db.scalar(select(User).where(User.email == "demo@terravant.local")):
        u = User(full_name="Demo Farmer", email="demo@terravant.local", password_hash=hash_password("Demo-passw0rd!"),
                 roles=[db.scalar(select(Role).where(Role.name == "farmer"))])
        db.add(u); db.flush()
        farm = Farm(owner_id=u.id, farm_name="Demo Farm", location="Sahiwal, Punjab", area=25, area_unit="acre")
        db.add(farm); db.flush()
        f = Field(farm_id=farm.id, field_name="Block A", area=10, soil_type="loam", latitude=30.6682, longitude=73.1114)
        db.add(f); db.flush()
        db.add(SoilRecord(field_id=f.id, nitrogen=28, phosphorus=6, potassium=95, ph=8.0))
        db.commit()
print("Demo user: demo@terravant.local / Demo-passw0rd!")
