import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

message = Mail(
    from_email=os.getenv("SENDGRID_FROM_EMAIL"),
    to_emails=os.getenv("TEST_EMAIL"),
    subject="LaunchMind Test Email",
    html_content="<h1>It works!</h1><p>Your Marketing Agent can send emails.</p>"
)

sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
response = sg.send(message)
print(f"Status code: {response.status_code}")
print("Email sent successfully!" if response.status_code == 202 else "Something went wrong")