import os

def send_reset_email(to_email, username, reset_code):
    """Send a password reset email via Resend API. Returns True on success."""
    
    api_key = os.getenv("RESEND_API_KEY", "")
    
    # Fallback for Streamlit Cloud secrets
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("RESEND_API_KEY", "")
        except:
            pass
            
    if not api_key:
        return False
    
    try:
        import requests
    except ImportError:
        return False
    
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
    
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "InvoiceAI <onboarding@resend.dev>",
        "to": [to_email],
        "subject": "InvoiceAI — Passwort zurücksetzen",
        "html": html_body
    }
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Email error: {e}")
        return False
