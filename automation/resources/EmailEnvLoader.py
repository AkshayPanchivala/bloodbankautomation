import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

class EmailEnvLoader:
    def load_email_credentials_from_env(self, env_path):
        # Load the .env file
        load_dotenv(dotenv_path=env_path)
        
        # Retrieve the variables
        email_username = os.getenv('EMAIL_USERNAME')
        email_password = os.getenv('EMAIL_PASSWORD')
        email_host = os.getenv('EMAIL_HOST')
        email_port = int(os.getenv('EMAIL_PORT', 587))
        
        return {
            'username': email_username,
            'password': email_password,
            'host': email_host,
            'port': email_port
        }

    def send_smtp_email(self, env_path, to_email, subject, body):
        creds = self.load_email_credentials_from_env(env_path)
        
        msg = MIMEMultipart()
        msg['From'] = creds['username']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(creds['host'], creds['port'])
            server.starttls()
            server.login(creds['username'], creds['password'])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            raise e

