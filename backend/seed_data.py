"""
Populate lookup/reference data: expense categories, bin providers, and a
handful of sample bin collection schedules (Requirement 3). Bin schedule
data isn't available via any free public API, so it's entered manually here
based on publicly published provider information - replace/extend the
SAMPLE_SCHEDULES list with real data for the areas you want to demo.

Run with: python seed_data.py
"""
from app import create_app
from extensions import db
from models import Category, BinProvider, BinSchedule

DEFAULT_CATEGORIES = [
    "Groceries", "Rent", "Transport", "Entertainment", "Utilities", "Other",
]

DEFAULT_PROVIDERS = ["Greyhound", "Panda", "Thorntons"]

# (eircode_prefix, provider_name, bin_type, collection_weekday[0=Mon], frequency_weeks)
SAMPLE_SCHEDULES = [
    ("D02", "Panda", "general", 0, 1),      # Monday, weekly
    ("D02", "Panda", "recycling", 0, 2),    # Monday, fortnightly
    ("D02", "Panda", "organic", 3, 1),      # Thursday, weekly
    ("D04", "Greyhound", "general", 1, 1),  # Tuesday, weekly
    ("D04", "Greyhound", "recycling", 1, 2),
    ("R95", "Thorntons", "general", 2, 1),  # Wednesday, weekly
    ("R95", "Thorntons", "recycling", 2, 2),
    ("R95", "Thorntons", "organic", 4, 1),  # Friday, weekly
]


def run_seed():
    app = create_app()
    with app.app_context():
        for name in DEFAULT_CATEGORIES:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name))

        for name in DEFAULT_PROVIDERS:
            if not BinProvider.query.filter_by(name=name).first():
                db.session.add(BinProvider(name=name))

        db.session.commit()

        provider_by_name = {p.name: p.id for p in BinProvider.query.all()}

        for prefix, provider_name, bin_type, weekday, freq in SAMPLE_SCHEDULES:
            provider_id = provider_by_name[provider_name]
            exists = BinSchedule.query.filter_by(
                eircode_prefix=prefix, provider_id=provider_id, bin_type=bin_type
            ).first()
            if not exists:
                db.session.add(BinSchedule(
                    eircode_prefix=prefix,
                    provider_id=provider_id,
                    bin_type=bin_type,
                    collection_weekday=weekday,
                    frequency_weeks=freq,
                ))

        db.session.commit()
        print("Seed data inserted.")


if __name__ == "__main__":
    run_seed()
