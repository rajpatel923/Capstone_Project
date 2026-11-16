# FRZR BURN — Admin Guide

FRZR BURN is a smart fridge reward system for CTF/cyber range courses. Students earn credits by completing challenges on the cyber range. Credits unlock access to a smart fridge via a keypad using their Member ID and a TOTP code from their authenticator app.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Prerequisites](#2-prerequisites)
3. [First-Time Setup](#3-first-time-setup)
4. [Environment Variables](#4-environment-variables)
5. [Starting and Stopping](#5-starting-and-stopping)
6. [Admin Dashboard](#6-admin-dashboard)
7. [Enrolling Students](#7-enrolling-students)
8. [Email Setup](#8-email-setup)
9. [Cyber Range Integration](#9-cyber-range-integration)
10. [TOTP Management](#10-totp-management)
11. [Credit System](#11-credit-system)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. System Overview

```
┌─────────────────┐     webhook      ┌──────────────────┐
│  Cyber Range    │ ──────────────▶  │  FRZR BURN API   │
│  (port 5050)    │  HMAC-signed     │  (port 8000)     │
└─────────────────┘                  └────────┬─────────┘
                                              │
┌─────────────────┐                  ┌────────▼─────────┐
│  Admin Dashboard│ ◀──────────────  │   PostgreSQL DB  │
│  (port 3000)    │                  └──────────────────┘
└─────────────────┘
         │  enrolls students
         ▼
┌─────────────────┐
│  Email (SMTP)   │  → student gets Member ID + secret key
└─────────────────┘
```

**Services and ports**

| Service | URL | Purpose |
|---|---|---|
| Admin Dashboard | http://localhost:3000 | Manage students, view ledger |
| API | http://localhost:8000 | Backend (also used by range) |
| Cyber Range (demo) | http://localhost:5050 | CTF challenge site |
| MailHog (dev only) | http://localhost:8025 | View outgoing emails locally |

**How the full flow works**

1. Admin enrolls students (individually or via CSV) → enrollment email sent
2. Student gets email with their **4-digit Member ID** and **TOTP secret key**
3. Student adds the secret key to Google Authenticator or Authy
4. Student registers on the Cyber Range (link in email, Member ID pre-filled)
5. Student completes challenges → range fires a webhook → credits added to ledger
6. Student visits the fridge, enters Member ID + 6-digit TOTP code → unlocked

---

## 2. Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

---

## 3. First-Time Setup

**Clone the repository**

```bash
git clone <repo-url>
cd Capstone_Project
```

**Copy and fill in the environment file**

```bash
cp .env.example .env   # if .env.example exists, otherwise edit .env directly
```

Fill in the required values — see [Section 4](#4-environment-variables).

**Generate a TOTP encryption key**

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the output as `TOTP_ENCRYPTION_KEY` in `.env`.

**Start everything**

```bash
docker compose up
```

On the first run Docker will build all images and run database migrations automatically. This takes ~2 minutes.

**Create an admin account**

1. Go to http://localhost:3000
2. Sign up with your email via Clerk
3. In the [Clerk Dashboard](https://dashboard.clerk.com), find your user → **Public Metadata** → set:
   ```json
   { "role": "admin" }
   ```
4. Refresh the dashboard — you now have full access.

---

## 4. Environment Variables

All variables live in `.env` at the project root. Docker Compose reads this file automatically.

### Required

| Variable | Description |
|---|---|
| `CLERK_SECRET_KEY` | From Clerk Dashboard → API Keys |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | From Clerk Dashboard → API Keys |
| `TOTP_ENCRYPTION_KEY` | Fernet key (see generation command above) |
| `RANGE_WEBHOOK_SECRET` | A shared secret between the API and the cyber range. Set the same value in both. Any random string works. |

### Database

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `postgres` | DB username |
| `POSTGRES_PASSWORD` | `postgres` | DB password |
| `POSTGRES_DB` | `fridge_dev` | Database name |

### SMTP (Email)

| Variable | Default | Description |
|---|---|---|
| `SMTP_HOST` | `mailhog` | SMTP server hostname |
| `SMTP_PORT` | `1025` | SMTP port (587 for Brevo/Gmail) |
| `SMTP_USERNAME` | — | SMTP login |
| `SMTP_PASSWORD` | — | SMTP password or API key |
| `SMTP_STARTTLS` | `false` | Set `true` for Brevo/Gmail |
| `SMTP_FROM` | — | Sender email address (must be verified with your SMTP provider) |
| `SMTP_FROM_NAME` | `FRZR BURN` | Sender display name |

### Cyber Range

| Variable | Default | Description |
|---|---|---|
| `RANGE_SITE_URL` | `http://localhost:5050` | Public URL of the cyber range — embedded in enrollment emails |
| `RANGE_SECRET_KEY` | `dev-secret-change-me` | Flask session secret for the demo range site |

### Optional Tuning

| Variable | Default | Description |
|---|---|---|
| `CREDIT_CONVERSION_RATE` | `10` | Points per credit (e.g. 10 means 50 pts = 5 credits) |
| `RATE_LIMIT_PER_MINUTE` | `10` | API rate limit per IP |

---

## 5. Starting and Stopping

```bash
# Start all services (runs in foreground, Ctrl+C to stop)
docker compose up

# Start in background
docker compose up -d

# Stop everything
docker compose down

# Stop and wipe the database (destructive)
docker compose down -v
```

If the database container fails with **"no space left on device"**, free up Docker's disk usage:

```bash
docker system prune -a --volumes
```

---

## 6. Admin Dashboard

Go to **http://localhost:3000** and log in.

### Students tab
- View all enrolled students, their Member ID, credit balance, and active status
- Click a student to see their full credit ledger and transaction history
- Edit name/email or toggle active/inactive
- Reset a student's TOTP secret (generates a new QR code shown once)
- Delete a student permanently

### Devices tab
- Manage registered fridge devices and their API keys

### Unlock Events tab
- View a log of every fridge unlock attempt

---

## 7. Enrolling Students

### Single student

Dashboard → Students → **New Student**  
Fill in full name and email → Submit.

The student receives an enrollment email containing:
- Their **4-digit Member ID**
- Their **TOTP secret key** (to enter in their authenticator app)
- A QR code (alternative to the secret key)
- A direct link to register on the Cyber Range (Member ID pre-filled)

### Bulk import via CSV

Dashboard → Students → **Import CSV**

The importer accepts three formats:

**Generic (simplest)**
```csv
Name,Email
Jane Doe,jane@university.edu
John Smith,john@university.edu
```

**Canvas People export** — works directly from Canvas → People → Export  
**Canvas Gradebook export** — works directly from Canvas → Grades → Export

Rows with blank name or email are skipped. Duplicate emails are skipped with a reason shown in the results table.

> **Note:** Bulk import requires SMTP to be configured. If `SMTP_HOST` is not set, all rows will be skipped — accounts are only created when the enrollment email can be delivered.

---

## 8. Email Setup

### Local development (MailHog)

By default, emails are captured by MailHog and never sent to real inboxes.  
View captured emails at **http://localhost:8025**.

Your `.env` defaults:
```env
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_STARTTLS=false
```

### Production email with Brevo (free tier — 300 emails/day)

1. Sign up at **brevo.com** (no credit card required)
2. Go to **SMTP & API** → **SMTP** tab → generate a key
3. Go to **Senders & IPs** → verify your sender email address
4. Update `.env`:

```env
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=your-brevo-login@example.com
SMTP_PASSWORD=your-brevo-smtp-key
SMTP_STARTTLS=true
SMTP_FROM=your-verified-sender@example.com
SMTP_FROM_NAME=FRZR BURN
```

5. Restart: `docker compose down && docker compose up`

### Production email with Gmail

1. Enable **2-Step Verification** on your Google account
2. Go to **App Passwords** → generate one for "Mail"
3. Update `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=yourname@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_STARTTLS=true
SMTP_FROM=yourname@gmail.com
```

---

## 9. Cyber Range Integration

The cyber range awards credits to students by calling the FRZR BURN API when a flag is captured.

### Webhook endpoint

```
POST http://localhost:8000/events/flag-captured
```

**Authentication** — either:
- Header `X-Range-Signature: sha256=<hmac-sha256-hex>` (preferred)
- Header `Authorization: Bearer <RANGE_WEBHOOK_SECRET>`

**Payload**
```json
{
  "range_challenge_id": "web-01",
  "title": "SQL Injection 101",
  "points": 50,
  "student_member_id": "0636"
}
```

Credits awarded = `points ÷ CREDIT_CONVERSION_RATE` (default: 50 pts → 5 credits).  
A 1-hour unlock eligibility window is also granted.

### Demo Cyber Range

A demo range site is included at `./demo_cyber_range` for testing.  
It runs at **http://localhost:5050** automatically with `docker compose up`.

**To test end-to-end:**

1. Enroll a student via the dashboard
2. Open **http://localhost:8025** (MailHog) — find the enrollment email
3. Click the **"Register on the Cyber Range"** link in the email (Member ID is pre-filled)
4. Log in to the range → solve a challenge → submit the flag
5. Go back to the dashboard → Students → click the student → verify credits in the ledger

### Connecting a real cyber range

Set the same `RANGE_WEBHOOK_SECRET` on both systems. The range must send a valid HMAC-SHA256 signature or Bearer token with every webhook call.

---

## 10. TOTP Management

Students use Google Authenticator or Authy with a **60-second** TOTP code.

### Setting up (student instructions)

1. Install **Google Authenticator** or **Authy**
2. Tap **Add account** → **Enter a setup key**
3. Enter the account name (e.g. their Member ID) and paste the **Secret Key** from the enrollment email
4. Set type to **Time-based**, interval **60 seconds**

### Resetting a student's TOTP

If a student loses access to their authenticator:

1. Dashboard → Students → click the student
2. Click **Reset TOTP** → a new QR code is shown once
3. Have the student scan the QR code or manually enter the new secret key

> The old code stops working immediately after reset.

---

## 11. Credit System

**Conversion rate:** 10 points = 1 credit (configurable via `CREDIT_CONVERSION_RATE`)

| Points | Credits |
|---|---|
| 10 | 1 |
| 20 | 2 |
| 50 | 5 |
| 100 | 10 |

Each solve also grants a **1-hour unlock eligibility window** — the student can visit the fridge within that hour.

The full ledger for each student is visible in the dashboard under their profile.

---

## 12. Troubleshooting

### API container exits immediately on startup

**Error:** `NameError: name 'Path' is not defined`  
**Fix:** Ensure `from pathlib import Path` is in `backend/app/core/config.py`. This was a known bug that has been fixed.

**Error:** `CLERK_SECRET_KEY is required` or `TOTP_ENCRYPTION_KEY is required`  
**Fix:** These values are missing from `.env`. Fill them in and restart.

### No space left on device

```bash
docker system prune -a --volumes
docker compose up
```

### Bulk import — all rows skipped

SMTP is not configured. Set `SMTP_HOST` in `.env` and restart. Accounts are only created when the enrollment email can be delivered.

### Webhook returns 401

The `RANGE_WEBHOOK_SECRET` in `.env` doesn't match what the range site is using. Both must be identical. After changing, restart both services.

### Webhook returns 404 — Student not found

The `student_member_id` in the webhook payload doesn't match any student in the database. Check the student's exact 4-digit Member ID in the dashboard.

### Student TOTP codes rejected at the fridge

- Codes generated before `TOTP_INTERVAL` was changed to 60 seconds will fail — reset the student's TOTP
- Ensure the student's authenticator app is set to **60-second** interval (not the default 30)
- The fridge firmware must also use `TOTP_INTERVAL = 60`

### Email delivered but QR code doesn't show

Some email clients block embedded images. The enrollment email includes both a QR code and the **plain-text secret key** — students can use either.
