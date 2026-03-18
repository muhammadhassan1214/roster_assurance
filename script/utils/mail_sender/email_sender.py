import os
import requests
from dotenv import load_dotenv


load_dotenv()
URL = "https://api.brevo.com/v3/smtp/email"
headers = {
    "accept": "application/json",
    "api-key": os.getenv("BREVO_API_KEY"),
    "content-type": "application/json"
}


def _build_recipients(receiver_emails):
    if isinstance(receiver_emails, str):
        receiver_emails = [receiver_emails]
    recipients = []
    for email in receiver_emails or []:
        email = (email or "").strip()
        if email:
            recipients.append({"email": email})
    return recipients


def send_bulk_email(receiver_emails, html_content, subject):
    recipients = _build_recipients(receiver_emails)
    if not recipients:
        print("No valid recipient emails provided.")
        return

    payload = {
        "sender": {
            "name": "Code Blue CPR Services",
            "email": os.getenv("SENDER_EMAIL")
        },
        "to": recipients,
        "subject": subject,
        "htmlContent": html_content
    }

    try:
        response = requests.post(URL, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"Email sent successfully to {len(recipients)} recipient(s)!")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Connection Error: {e}")


def send_email(receiver_emails, html_content, subject="Immediate Action Required – Roster Submission and Course Records"):
    return send_bulk_email(receiver_emails, html_content, subject)
