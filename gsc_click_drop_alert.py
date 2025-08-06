import datetime
import smtplib
from email.mime.text import MIMEText
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load credentials from environment variable
SERVICE_ACCOUNT_INFO = json.loads(os.environ['GSC_CREDENTIALS'])
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
SITE_URL = 'https://coalitiontechnologies.com/'  # Replace with your domain
ALERT_EMAIL = 'deepak.garg@coalitiontechnologies.com'        # Your email to receive alert
GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_PASS = os.environ['GMAIL_PASS']
DROP_THRESHOLD = 0.3  # 30%

def get_clicks(service, start_date, end_date):
    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['date'],
    }
    response = service.searchanalytics().query(siteUrl=SITE_URL, body=request).execute()
    return sum(row['clicks'] for row in response.get('rows', []))

def send_email_alert(old_clicks, new_clicks, drop_pct):
    msg = MIMEText(f"""
🚨 GSC Alert: Drop in Clicks Detected

Old Clicks: {old_clicks}
New Clicks: {new_clicks}
Drop: {drop_pct*100:.2f}%

Check Google Search Console for details.
""")
    msg['Subject'] = '⚠️ GSC Clicks Drop Alert'
    msg['From'] = GMAIL_USER
    msg['To'] = ALERT_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)

def main():
    creds = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    service = build('searchconsole', 'v1', credentials=creds)

    today = datetime.date.today()
    yesterday = str(today - datetime.timedelta(days=1))
    day_before = str(today - datetime.timedelta(days=2))

    clicks_yesterday = get_clicks(service, yesterday, yesterday)
    clicks_day_before = get_clicks(service, day_before, day_before)

    if clicks_day_before == 0:
        return

    drop_pct = (clicks_day_before - clicks_yesterday) / clicks_day_before

    if drop_pct >= DROP_THRESHOLD:
        send_email_alert(clicks_day_before, clicks_yesterday, drop_pct)

if __name__ == '__main__':
    main()
