from app import create_app
from extensions import db
from models import Category, BinProvider, BinSchedule

DEFAULT_CATEGORIES = [
    "Groceries", "Rent", "Transport", "Entertainment", "Utilities", "Other",
]

DEFAULT_PROVIDERS = ["Greyhound"]

# (eircode_prefix, provider_name, bin_type, collection_weekday[0=Mon], frequency_weeks)
_AREA_WEEKDAYS = [
    ("D01", 0), ("D02", 1), ("D03", 2), ("D04", 3), ("D06", 4), ("D6W", 0),
    ("D07", 1), ("D08", 2), ("D09", 3), ("D11", 4), ("D12", 0), ("D13", 1),
    ("D14", 2), ("D15", 3), ("D24", 4), ("A96", 1),
]
_BIN_TYPES = ["general", "organic", "recycling"]

SAMPLE_SCHEDULES = [
    (prefix, "Greyhound", bin_type, weekday, 2)
    for prefix, weekday in _AREA_WEEKDAYS
    for bin_type in _BIN_TYPES
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
            existing = BinSchedule.query.filter_by(
                eircode_prefix=prefix, provider_id=provider_id, bin_type=bin_type
            ).first()
            # Update in place (not just skip) so re-running this script picks up
            # revised weekday/frequency values instead of leaving stale rows.
            if existing:
                existing.collection_weekday = weekday
                existing.frequency_weeks = freq
            else:
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
