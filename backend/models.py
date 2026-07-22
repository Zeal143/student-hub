"""
SQLAlchemy models - one class per database table.

Each model has a `to_dict()` method that converts it into a plain dict of
JSON-serialisable values. Every blueprint uses this instead of hand-building
response dictionaries, so the JSON shape returned by the API for e.g. an
Expense is defined in exactly one place.

Tables are created from these classes via `db.create_all()` (see app.py /
the README) rather than hand-written SQL migrations - fine for a student
project, but a production app would normally use Flask-Migrate/Alembic so
schema changes are versioned instead of just "whatever the models currently
say".
"""
from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)  # bcrypt hash - see blueprints/auth.py

    # Bin schedule tracker settings (Requirement 3). Nullable because using
    # the bin tracker is optional - a user might only use the expense tracker.
    eircode = db.Column(db.String(10), nullable=True)
    bin_provider_id = db.Column(db.Integer, db.ForeignKey("bin_providers.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # cascade="all, delete-orphan": deleting a User also deletes all of their
    # expenses/budgets/savings goals, so no orphaned rows are left behind
    # pointing at a user_id that no longer exists.
    expenses = db.relationship("Expense", backref="user", lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship("Budget", backref="user", lazy=True, cascade="all, delete-orphan")
    savings_goals = db.relationship("SavingsGoal", backref="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        # Deliberately excludes password_hash - this is what gets sent to
        # the frontend and cached in localStorage, so no password data
        # (hashed or otherwise) should ever appear in it.
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "eircode": self.eircode,
            "bin_provider_id": self.bin_provider_id,
        }


class Category(db.Model):
    """A fixed set of expense categories (Groceries, Rent, ...) shared by all users - see seed_data.py."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Numeric, not Float - avoids binary floating-point rounding errors on money
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "amount": float(self.amount),  # Decimal isn't JSON-serialisable directly, so convert for the API response
            "description": self.description,
            "date": self.date.isoformat(),
        }


class Budget(db.Model):
    """A user's monthly spending limit for one category (Requirement 2)."""

    __tablename__ = "budgets"
    # One budget per user per category - POST /api/budgets relies on this to
    # decide whether to insert a new row or update the existing one.
    __table_args__ = (db.UniqueConstraint("user_id", "category_id", name="uq_user_category_budget"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    monthly_limit = db.Column(db.Numeric(10, 2), nullable=False)

    category = db.relationship("Category")

    def to_dict(self):
        # Note: this does NOT include `spent`/`remaining`/`over_budget` -
        # those are calculated on the fly in blueprints/budgets.py by
        # summing that category's expenses for the current month, since
        # "amount spent so far" isn't a stored value, it's a live total.
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "monthly_limit": float(self.monthly_limit),
        }


class SavingsGoal(db.Model):
    """A named target a user is saving towards (Requirement 2), e.g. 'Summer trip'."""

    __tablename__ = "savings_goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    current_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    target_date = db.Column(db.Date, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "target_amount": float(self.target_amount),
            "current_amount": float(self.current_amount),
            "target_date": self.target_date.isoformat() if self.target_date else None,
            # Guard against divide-by-zero: target_amount must be > 0 at
            # creation time (see blueprints/savings.py), but this keeps
            # to_dict() safe even if that ever changes.
            "progress_pct": round(
                (float(self.current_amount) / float(self.target_amount)) * 100, 1
            ) if float(self.target_amount) > 0 else 0,
        }


class BinProvider(db.Model):
    """A household waste collection company, e.g. Panda, Greyhound, Thorntons."""

    __tablename__ = "bin_providers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class BinSchedule(db.Model):
    """
    Seed data row: for a given provider + Eircode routing-key prefix (first 3
    chars, e.g. 'R95'), a bin type is collected on a given weekday at a given
    frequency. Real-world data would come from each provider's published
    calendar; here it is entered manually as seed data (see seed_data.py).
    """
    __tablename__ = "bin_schedules"

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey("bin_providers.id"), nullable=False)
    eircode_prefix = db.Column(db.String(3), nullable=False, index=True)
    bin_type = db.Column(db.String(20), nullable=False)  # general | recycling | organic
    collection_weekday = db.Column(db.Integer, nullable=False)  # 0=Mon ... 6=Sun
    frequency_weeks = db.Column(db.Integer, nullable=False, default=1)  # 1=weekly, 2=fortnightly

    provider = db.relationship("BinProvider")

    # Used by the frontend to colour-code each bin type consistently across
    # every page (dashboard, bins page) without hardcoding colours in the JS.
    BIN_COLOURS = {
        "general": "#4a4a4a",
        "recycling": "#2e7d32",
        "organic": "#8d6e63",
    }

    def to_dict(self):
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "provider_name": self.provider.name if self.provider else None,
            "bin_type": self.bin_type,
            "colour": self.BIN_COLOURS.get(self.bin_type, "#000000"),
            "collection_weekday": self.collection_weekday,
            "frequency_weeks": self.frequency_weeks,
        }


class Reminder(db.Model):
    """
    A record that a bin-collection reminder email has already been sent, so
    the daily job in reminders.py never emails the same user about the same
    collection twice (e.g. if it's run more than once on the same day).
    """

    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bin_schedule_id = db.Column(db.Integer, db.ForeignKey("bin_schedules.id"), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    collection_date = db.Column(db.Date, nullable=False)
