"""
Background job (Requirement 3 / Requirement 6): once a day, check every user's
upcoming bin collections and email anyone whose next collection is tomorrow.

Run standalone with `python reminders.py`, or wire `run_reminder_check` into
APScheduler / a cron job / an AWS EventBridge-triggered Lambda in production.
"""
import smtplib
from datetime import date, timedelta
from email.mime.text import MIMEText

from app import create_app
from extensions import db
from models import User, BinSchedule, Reminder
from blueprints.bins import _next_occurrences
from config import Config


def send_email(to_address, subject, body):
    if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
        print(f"[reminders] SMTP not configured - would have emailed {to_address}: {subject}")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"{Config.SMTP_FROM_NAME} <{Config.SMTP_USERNAME}>"
    msg["To"] = to_address

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
        server.starttls()
        server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        server.sendmail(Config.SMTP_USERNAME, [to_address], msg.as_string())


def run_reminder_check():
    app = create_app()
    with app.app_context():
        tomorrow = date.today() + timedelta(days=1)
        users = User.query.filter(User.eircode.isnot(None), User.bin_provider_id.isnot(None)).all()

        for user in users:
            eircode_prefix = user.eircode.replace(" ", "")[:3]
            schedules = BinSchedule.query.filter_by(
                eircode_prefix=eircode_prefix, provider_id=user.bin_provider_id
            ).all()

            for schedule in schedules:
                next_date = _next_occurrences(schedule.collection_weekday, schedule.frequency_weeks, count=1)[0]
                if next_date != tomorrow:
                    continue

                already_sent = Reminder.query.filter_by(
                    user_id=user.id, bin_schedule_id=schedule.id, collection_date=next_date
                ).first()
                if already_sent:
                    continue

                send_email(
                    user.email,
                    subject=f"Reminder: {schedule.bin_type} bin collection tomorrow",
                    body=(
                        f"Hi {user.name},\n\n"
                        f"Your {schedule.bin_type} bin is due for collection tomorrow "
                        f"({next_date.strftime('%A %d %B %Y')}).\n\n"
                        f"- Irish International Student Hub"
                    ),
                )
                db.session.add(Reminder(
                    user_id=user.id,
                    bin_schedule_id=schedule.id,
                    collection_date=next_date,
                ))
                db.session.commit()
                print(f"[reminders] Sent {schedule.bin_type} reminder to {user.email}")


if __name__ == "__main__":
    run_reminder_check()
