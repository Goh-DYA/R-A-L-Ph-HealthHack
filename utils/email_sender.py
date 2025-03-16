# Email functionality for RALPh.

import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT


def is_valid_email(email):
    """
    Validate an email address.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email is valid
    """
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None


def send_email_with_pdf(pdf_path, recipient_email):
    """
    Send PDF via email.
    
    Args:
        pdf_path (str): Path to PDF file
        recipient_email (str): Recipient's email address
        
    Returns:
        str: Success message or error
    """
    print("Attempting to send email...")
    try:
        # Validate recipient email
        if not is_valid_email(recipient_email):
            return "Invalid email address. Please provide a valid email."

        # Validate PDF file exists
        if not os.path.exists(pdf_path):
            return f"PDF file not found at {pdf_path}"

        # Email configuration
        sender_email = EMAIL_SENDER
        sender_password = EMAIL_PASSWORD
        smtp_server = EMAIL_SMTP_SERVER
        smtp_port = EMAIL_SMTP_PORT

        # Email subject and body
        subject = "RALPh Chatbot Conversation PDF"
        body = "Please find attached the PDF of your chatbot conversation."

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = sender_email.strip()
        msg['To'] = recipient_email.strip()
        msg['Subject'] = subject
        msg.attach(MIMEText(body.encode('utf-8'), 'plain', 'utf-8'))

        # Attach the PDF file
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(pdf_path)}",
            )
            msg.attach(part)

        # Connect to the SMTP server and send the email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()

        return f"Email sent successfully to {recipient_email}!"
    except Exception as e:
        return f"Error while sending email: {e}"