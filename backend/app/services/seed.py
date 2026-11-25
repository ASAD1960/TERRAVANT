from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Crop, Role

ROLES = {
    "farmer": "Manages farms and receives agricultural intelligence",
    "business": "Manages agricultural operations",
    "advisor": "Reviews agricultural information and advises, where authorized",
    "admin": "Manages users, permissions and configuration",
    "operator": "Monitors deployed models and system health",
}

CROPS = [
    ("wheat", "cereal", "rabi", "Main winter staple of Punjab."),
    ("rice", "cereal", "kharif", "Basmati and coarse varieties; water-intensive."),
    ("maize", "cereal", "kharif", "Spring and autumn crops."),
    ("cotton", "fibre", "kharif", "Major cash crop of southern Punjab."),
    ("sugarcane", "cash", "annual", "Long-duration cash crop."),
    ("mustard", "oilseed", "rabi", "Winter oilseed."),
    ("chickpea", "pulse", "rabi", "Rain-fed and barani areas."),
    ("potato", "vegetable", "rabi", "Autumn and spring crops."),
    ("sunflower", "oilseed", "kharif", "Spring and autumn oilseed."),
]


def seed_reference_data(db: Session) -> None:
    have = {r.name for r in db.scalars(select(Role))}
    for name, desc in ROLES.items():
        if name not in have:
            db.add(Role(name=name, description=desc))
    have_c = {c.crop_name for c in db.scalars(select(Crop))}
    for name, cat, season, desc in CROPS:
        if name not in have_c:
            db.add(Crop(crop_name=name, category=cat, growing_season=season, description=desc))
    db.commit()
