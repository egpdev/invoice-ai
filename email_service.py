import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_reset_email(to_email, username, reset_code):
    """Send a password reset email. Returns True on success."""
    
    smtp_email = os.getenv("SMTP_EMAIL", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    
    if not smtp_email or not smtp_password:
        return False
    
    subject = "InvoiceAI — Passwort zurücksetzen"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #0b1120; color: #e2e8f0; padding: 2rem;">
        <div style="max-width: 500px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 2rem; border: 1px solid #334155;">
            <h2 style="color: #60a5fa; text-align: center;">🏛️ InvoiceAI</h2>
            <p>Hallo <strong>{username}</strong>,</p>
            <p>Sie haben eine Passwortzurücksetzung angefordert. Hier ist Ihr Reset-Code:</p>
            <div style="background: #0f172a; border: 2px solid #3b82f6; border-radius: 12px; padding: 1.2rem; text-align: center; margin: 1.5rem 0;">
                <span style="font-size: 1.8rem; font-weight: 800; color: #60a5fa; letter-spacing: 3px;">{reset_code}</span>
            </div>
            <p>Kopieren Sie diesen Code und fügen Sie ihn auf der InvoiceAI-Website ein.</p>
            <p style="color: #94a3b8; font-size: 0.85rem;">Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail einfach.</p>
            <hr style="border-color: #334155; margin: 1.5rem 0;">
            <p style="color: #64748b; font-size: 0.8rem; text-align: center;">
                🔐 InvoiceAI — KI-gestützte Rechnungsverarbeitung
            </p>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_email
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False
