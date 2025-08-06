import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import smtplib
from email.mime.text import MIMEText
from datetime import date, timedelta

# Load credentials from file
creds = service_account.Credentials.from_service_account_file(
    "secrets/service_account.json",
    scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
)

webmasters = build("searchconsole", "v1", credentials=creds)

# Replace with your property
site_url = "https://libertypainting.net/"

# Date range
today = date.today()
yesterday = today - timedelta(days=1)
day_before = today - timedelta(days=2)

def get_clicks(date_str):
    response = webmasters.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": date_str,
            "endDate": date_str,
            "dimensions": ["date"],
        },
    ).execute()
    if "rows" in response:
        return response["rows"][0]["clicks"]
    return 0

clicks_yesterday = get_clicks(str(yesterday))
clicks_day_before = get_clicks(str(day_before))

# Send alert if drop is more than 30%
if clicks_day_before > 0 and (clicks_yesterday / clicks_day_before) < 0.7:
    drop = clicks_day_before - clicks_yesterday
    drop_pct = round((drop / clicks_day_before) * 100, 2)
    msg = MIMEText(f"⚠️ Alert: Clicks dropped by {drop_pct}%!\n\nYesterday: {clicks_yesterday}\nDay Before: {clicks_day_before}")
    msg["Subject"] = "GSC Alert: Significant Click Drop"
    msg["From"] = os.environ["GMAIL_USER"]
    msg["To"] = os.environ["GMAIL_USER"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["GMAIL_USER"], os.environ["GMAIL_PASS"])
        server.send_message(msg)
