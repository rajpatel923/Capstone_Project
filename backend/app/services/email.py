import asyncio
import base64
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    totp_secret: str,
    provisioning_uri: str,
    qr_b64: str,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Welcome to FRZR BURN — Your TOTP Setup"
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from}>"

    range_url = f"{settings.range_site_url}/register?member_id={member_id}"

    plain = f"""Welcome to FRZR BURN, {full_name}!

Your Member ID : {member_id}
Your Secret Key: {totp_secret}

── Step 1: Set up your authenticator app ─────────────────
1. Install Google Authenticator or Authy on your phone.
2. Tap "Add account" → "Enter a setup key".
3. Enter your Member ID as the account name and paste the Secret Key above.
   Set the type to Time-based and the interval to 60 seconds.
4. At the fridge keypad, enter your 4-digit Member ID then the 6-digit code.

You can also scan the QR code in the HTML version of this email.

── Step 2: Join the Cyber Range ──────────────────────────
Register here (your Member ID is pre-filled):
{range_url}

Keep your Secret Key private — do not share it.
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
    <li>Tap <strong>Add account</strong> → <strong>Enter a setup key</strong>.</li>
    <li>Use your Member ID as the account name and enter the secret key below.</li>
    <li>Set type to <strong>Time-based</strong>, interval <strong>60 seconds</strong>.</li>
  </ol>

  <div style="background:#f4f4f5;border-radius:8px;padding:16px 20px;margin:20px 0;">
    <p style="margin:0 0 4px;font-size:0.8em;color:#666;text-transform:uppercase;letter-spacing:0.05em;">Your Secret Key</p>
    <p style="margin:0;font-family:monospace;font-size:1.4em;letter-spacing:0.2em;font-weight:700;word-break:break-all;">{totp_secret}</p>
    <p style="margin:8px 0 0;font-size:0.8em;color:#666;">Type this exactly into your authenticator app. Keep it private.</p>
  </div>

  <p style="font-size:0.85em;color:#666;">Or scan the QR code instead:</p>
  <div style="margin:12px 0 20px;text-align:center;">
    <img src="data:image/png;base64,{qr_b64}"
         alt="TOTP QR Code"
         width="200" height="200"
         style="border:1px solid #e4e4e7;padding:8px;border-radius:8px;background:#fff;" />
  </div>

  <h3>Join the Cyber Range</h3>
  <p>Complete challenges to earn more fridge credits. Your Member ID is pre-filled — just click the link below:</p>
  <a href="{range_url}"
     style="display:inline-block;background:#111;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:600;margin-bottom:8px;">
    Register on the Cyber Range →
  </a>
  <p style="font-size:0.8em;color:#999;margin-top:4px;">Or copy: <code style="font-size:0.9em;">{range_url}</code></p>

  <h3>Using the fridge</h3>
  <p>At the keypad: type your <strong>4-digit Member ID</strong>, then the <strong>6-digit code</strong> shown in your authenticator app. The code refreshes every 60 seconds.</p>

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
    totp_secret: str,
    provisioning_uri: str,
) -> bool:
    """Send TOTP enrollment email. Returns False if SMTP not configured. Raises on SMTP errors."""
    if not settings.smtp_host:
        return False

    qr_b64 = _generate_qr_base64(provisioning_uri)
    msg = _build_enrollment_email(full_name, member_id, totp_secret, provisioning_uri, qr_b64)
    msg["To"] = to_email

    def _send() -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_starttls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(msg["From"], [to_email], msg.as_string())

    await asyncio.to_thread(_send)
    return True
