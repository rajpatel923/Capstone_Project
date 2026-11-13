import base64
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import qrcode

from app.core.config import settings


def _generate_qr_base64(provisioning_uri: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _build_enrollment_email(
    full_name: str,
    member_id: str,
    provisioning_uri: str,
    qr_b64: str,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Welcome to FRZR BURN — Your TOTP Setup"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from}>"

    plain = f"""Welcome to FRZR BURN, {full_name}!

Your Member ID: {member_id}

To use the smart fridge:
1. Install Google Authenticator or Authy on your phone.
2. Scan the QR code in the HTML version of this email, or manually add this URI:
   {provisioning_uri}
3. At the fridge keypad, enter your 4-digit Member ID followed by the 6-digit code from your app.

This QR code is for your eyes only — do not share it.
"""

    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#111;">
  <h2 style="margin-bottom:4px;">Welcome to FRZR BURN, {full_name}!</h2>
  <p>You have been enrolled in the smart fridge reward system.</p>

  <div style="background:#f4f4f5;border-radius:8px;padding:16px 20px;margin:20px 0;">
    <p style="margin:0 0 4px;font-size:0.85em;color:#666;text-transform:uppercase;letter-spacing:0.05em;">Your Member ID</p>
    <p style="margin:0;font-family:monospace;font-size:2em;letter-spacing:0.15em;font-weight:700;">{member_id}</p>
    <p style="margin:8px 0 0;font-size:0.85em;color:#666;">You will need this every time you use the fridge keypad.</p>
  </div>

  <h3>Set up your authenticator app</h3>
  <ol style="line-height:1.8;">
    <li>Install <strong>Google Authenticator</strong> or <strong>Authy</strong> on your phone.</li>
    <li>Open the app and scan the QR code below:</li>
  </ol>

  <div style="margin:20px 0;text-align:center;">
    <img src="data:image/png;base64,{qr_b64}"
         alt="TOTP QR Code"
         width="220" height="220"
         style="border:1px solid #e4e4e7;padding:8px;border-radius:8px;background:#fff;" />
  </div>

  <p style="font-size:0.85em;color:#666;background:#f9f9f9;border:1px solid #e4e4e7;border-radius:6px;padding:12px;">
    <strong>Can&apos;t scan?</strong> Add this URI manually in your authenticator app:<br/>
    <code style="word-break:break-all;font-size:0.9em;">{provisioning_uri}</code>
  </p>

  <h3>Using the fridge</h3>
  <p>At the keypad: type your <strong>4-digit Member ID</strong>, then the <strong>6-digit code</strong> shown in your authenticator app. The code refreshes every 30 seconds.</p>

  <hr style="margin:28px 0;border:none;border-top:1px solid #e4e4e7;" />
  <p style="font-size:0.8em;color:#999;">Do not share your QR code or Member ID with others. Contact your professor to reset your TOTP if needed.</p>
</body>
</html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


async def send_enrollment_email(
    to_email: str,
    full_name: str,
    member_id: str,
    provisioning_uri: str,
) -> bool:
    """Send TOTP enrollment email. Returns False if SMTP not configured. Raises on SMTP errors."""
    if not settings.smtp_host:
        return False

    qr_b64 = _generate_qr_base64(provisioning_uri)
    msg = _build_enrollment_email(full_name, member_id, provisioning_uri, qr_b64)
    msg["To"] = to_email

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username or None,
        password=settings.smtp_password or None,
        start_tls=settings.smtp_starttls,
    )
    return True
