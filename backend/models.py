from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Bin schedule tracker settings
    eircode = db.Column(db.String(10), nullable=True)
    bin_provider_id = db.Column(db.Integer, db.ForeignKey("bin_providers.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    expenses = db.relationship("Expense", backref="user", lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship("Budget", backref="user", lazy=True, cascade="all, delete-orphan")
    savings_goals = db.relationship("SavingsGoal", backref="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "eircode": self.eircode,
            "bin_provider_id": self.bin_provider_id,
        }


class Category(db.Model):
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
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "amount": float(self.amount),
            "description": self.description,
            "date": self.date.isoformat(),
        }


class Budget(db.Model):
    __tablename__ = "budgets"
    __table_args__ = (db.UniqueConstraint("user_id", "category_id", name="uq_user_category_budget"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    monthly_limit = db.Column(db.Numeric(10, 2), nullable=False)

    category = db.relationship("Category")

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "monthly_limit": float(self.monthly_limit),
        }


class SavingsGoal(db.Model):
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
            "progress_pct": round(
                (float(self.current_amount) / float(self.target_amount)) * 100, 1
            ) if float(self.target_amount) > 0 else 0,
        }


class BinProvider(db.Model):
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
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bin_schedule_id = db.Column(db.Integer, db.ForeignKey("bin_schedules.id"), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    collection_date = db.Column(db.Date, nullable=False)
