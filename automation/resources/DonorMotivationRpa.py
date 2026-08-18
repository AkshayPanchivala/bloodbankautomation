import os
import pymongo
from datetime import datetime, timedelta, timezone
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

def send_motivation_email(email_address, user_name, days_since):
    """Sends a motivation email using SMTP."""
    # Load credentials from .env
    load_dotenv()
    
    email_user = os.getenv("EMAIL_USERNAME")
    email_pass = os.getenv("EMAIL_PASSWORD")
    email_host = os.getenv("EMAIL_HOST")
    email_port = os.getenv("EMAIL_PORT")

    if not all([email_user, email_pass, email_host, email_port]):
        print("Missing email credentials in .env file.")
        return False

    msg = EmailMessage()
    msg['Subject'] = f"We miss you, {user_name}! You're eligible to donate again."
    msg['From'] = email_user
    msg['To'] = email_address
    
    content = f"""Hello {user_name},

It has been {days_since} days since your last heroic blood donation. 
Since it has been more than 3 months, you are now fully eligible to donate blood again!

Your donation saves lives. Please visit the Blood Bank portal to schedule your next donation.

Thank you,
The Blood Bank Management Team
"""
    msg.set_content(content)

    try:
        with smtplib.SMTP(email_host, int(email_port)) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
        print(f"Motivation email successfully sent to {email_address}")
        return True
    except Exception as e:
        print(f"Failed to send email to {email_address}: {e}")
        return False

def check_and_send_motivation_emails():
    """Scans DB for 3-month old donations and sends emails."""
    MONGO_URI = "mongodb+srv://akshaypanchivala_db_user:akshaypanchivala_db_user@cluster0.klbtn0r.mongodb.net/blood_bank_management?retryWrites=true&w=majority&appName=Cluster0"
    
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client["blood_bank_management"]
        
        # Calculate the threshold date (90 days ago)
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        
        print(f"Scanning for Fulfilled donations before {ninety_days_ago}...")
        
        # Find donations that were fulfilled more than 89 days ago
        old_donations = db.blooddonates.find({
            "status": "Fulfilled",
            "createdAt": {"$lt": ninety_days_ago}
        })
        
        emails_sent = 0
        
        for donation in old_donations:
            user_id = donation.get("userId")
            if user_id:
                # We need to find the user to get their email
                user = db.users.find_one({"_id": user_id})
                if user:
                    email = user.get("email")
                    name = user.get("firstName", "Donor")
                    
                    # Calculate exact days
                    days_since = (datetime.now(timezone.utc) - donation["createdAt"].replace(tzinfo=timezone.utc)).days
                    
                    print(f"Found eligible donor: {email} (Last donation: {days_since} days ago)")
                    
                    # Send the email
                    success = send_motivation_email(email, name, days_since)
                    if success:
                        emails_sent += 1
                        
                        # Note: In a real system, you would mark a flag like "motivation_sent=True"
                        # on the user or donation record so you don't spam them every single day.
                        # For this automation test, we just send it.
                        
        print(f"Process complete. Total motivation emails sent: {emails_sent}")
        return emails_sent
        
    except Exception as e:
        print(f"RPA Error: {e}")
        return 0

if __name__ == "__main__":
    check_and_send_motivation_emails()
