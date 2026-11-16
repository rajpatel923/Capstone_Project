export type DocBlock =
  | { type: "paragraph"; text: string }
  | { type: "heading"; text: string }
  | { type: "list"; items: string[] }
  | { type: "steps"; items: string[] }
  | { type: "code"; label?: string; lines: string[] }
  | { type: "callout"; variant: "info" | "warning" | "tip"; text: string }
  | { type: "table"; headers: string[]; rows: string[][] }

export type DocSection = {
  id: string
  title: string
  description: string
  blocks: DocBlock[]
}

export const docSections: DocSection[] = [
  {
    id: "overview",
    title: "Overview",
    description: "What FRZR BURN is and how it works",
    blocks: [
      {
        type: "paragraph",
        text: "FRZR BURN is a CTF-gated smart mini-fridge reward system. Students earn fridge credits by completing cybersecurity challenges on a cyber range. Credits can be redeemed for items inside the fridge via a keypad using their Member ID and a TOTP code from their authenticator app.",
      },
      {
        type: "heading",
        text: "The three-layer system",
      },
      {
        type: "list",
        items: [
          "Cyber Range — students solve challenges, the range fires a signed webhook to the backend",
          "Backend API — validates webhooks, manages eligibility windows, tracks credits",
          "ESP32 Fridge — a keypad-and-servo lock that calls the backend to verify codes",
        ],
      },
      {
        type: "heading",
        text: "What admins can do",
      },
      {
        type: "list",
        items: [
          "Enroll students individually or via CSV bulk import",
          "Automatically email students their Member ID, TOTP secret key, and range registration link",
          "Monitor device heartbeat and firmware versions",
          "Review every unlock attempt in the audit log",
          "Manage fridge inventory and process credit redemptions",
          "Deactivate, edit, reset TOTP, or permanently delete any student",
        ],
      },
      {
        type: "callout",
        variant: "info",
        text: "Students never log in to this dashboard. Their only interaction with the system is at the fridge keypad, in their authenticator app, and on the cyber range website.",
      },
    ],
  },
  {
    id: "getting-started",
    title: "Getting Started",
    description: "Logging in and reading the dashboard",
    blocks: [
      {
        type: "paragraph",
        text: "Access the dashboard at your deployed frontend URL. Sign in with your admin Clerk account — only accounts with the admin role in publicMetadata can access the dashboard. Non-admin accounts are redirected to the sign-in page.",
      },
      {
        type: "heading",
        text: "Setting the admin role",
      },
      {
        type: "steps",
        items: [
          "Sign up at the dashboard URL with your email",
          "Open the Clerk Dashboard at dashboard.clerk.com",
          "Find your user → Public Metadata",
          'Set: { "role": "admin" }',
          "Refresh the FRZR BURN dashboard — you now have full access",
        ],
      },
      {
        type: "heading",
        text: "Dashboard overview",
      },
      {
        type: "table",
        headers: ["Card", "What it shows"],
        rows: [
          ["Total Students", "Number of enrolled students (shows 50+ if paginated)"],
          ["Active Students", "Students with active accounts who can unlock the fridge"],
          ["Devices", "Total number of registered ESP32 devices"],
          ["Online Now", "Devices that sent a heartbeat in the last 60 seconds"],
        ],
      },
      {
        type: "callout",
        variant: "tip",
        text: "Bookmark the dashboard URL and keep it open during CTF events — the device status and recent events update automatically.",
      },
    ],
  },
  {
    id: "enrolling-students",
    title: "Enrolling Students",
    description: "Adding students individually or via CSV bulk import",
    blocks: [
      {
        type: "paragraph",
        text: "Each student gets a unique auto-generated 4-digit Member ID and a TOTP secret sent to their email. There are two ways to enroll: individually for a single student, or via CSV for a whole class.",
      },
      {
        type: "callout",
        variant: "warning",
        text: "Student accounts are only created when the enrollment email can be delivered. SMTP must be configured before enrolling. If SMTP is not set up, all enrollments will be rejected.",
      },
      {
        type: "heading",
        text: "Single enrollment",
      },
      {
        type: "steps",
        items: [
          "Navigate to Students in the sidebar",
          "Click New Student in the top-right",
          "Enter the student's Full Name and Email address",
          "Click Enroll — the account is created and the enrollment email is sent automatically",
          "The admin sees a one-time QR code — this is a backup only. The student already has everything they need in their email.",
        ],
      },
      {
        type: "heading",
        text: "Bulk import via CSV",
      },
      {
        type: "steps",
        items: [
          "Navigate to Students → Import CSV",
          "Drop your CSV file or click Browse",
          "Preview the detected students — review for any warnings",
          "Click Import — each student is enrolled and emailed in one go",
          "The results table shows enrolled / skipped / error per row",
        ],
      },
      {
        type: "heading",
        text: "Supported CSV formats",
      },
      {
        type: "table",
        headers: ["Format", "Required columns"],
        rows: [
          ["Generic", "Name, Email"],
          ["Canvas People export", "Name, Email, Section"],
          ["Canvas Gradebook export", "Student, Email Address, SIS User ID"],
        ],
      },
      {
        type: "code",
        label: "Generic CSV example",
        lines: [
          "Name,Email",
          "Jane Doe,jane@university.edu",
          "John Smith,john@university.edu",
        ],
      },
      {
        type: "callout",
        variant: "tip",
        text: "Canvas People and Gradebook exports work directly — just download from Canvas and upload here without any editing.",
      },
      {
        type: "heading",
        text: "What the enrollment email contains",
      },
      {
        type: "list",
        items: [
          "The student's 4-digit Member ID",
          "Their TOTP secret key (to enter manually in their authenticator app)",
          "A QR code (alternative to the secret key)",
          "A direct link to register on the Cyber Range — Member ID is pre-filled in the form",
        ],
      },
    ],
  },
  {
    id: "totp-codes",
    title: "TOTP Codes & the Keypad",
    description: "How students set up their authenticator and unlock the fridge",
    blocks: [
      {
        type: "paragraph",
        text: "The fridge keypad accepts a 10-digit code: the student's 4-digit Member ID followed immediately by their current 6-digit TOTP code from their authenticator app. No spaces or separators.",
      },
      {
        type: "heading",
        text: "Code format",
      },
      {
        type: "code",
        label: "Example — member ID 1234, TOTP 567890",
        lines: [
          "Member ID:  1234",
          "TOTP code:  567890",
          "             ──────────",
          "Full code:  1234567890   ← type this, then press #",
        ],
      },
      {
        type: "heading",
        text: "Student setup instructions",
      },
      {
        type: "steps",
        items: [
          "Install Google Authenticator or Authy on your phone",
          "Tap Add account → Enter a setup key",
          "Use your Member ID as the account name",
          "Paste the Secret Key from your enrollment email",
          "Set type to Time-based, interval 60 seconds",
          "Tap Add — a 6-digit code will appear, refreshing every 60 seconds",
        ],
      },
      {
        type: "callout",
        variant: "warning",
        text: "The interval must be set to 60 seconds, not the default 30. Codes generated at 30 seconds will always be rejected at the fridge.",
      },
      {
        type: "heading",
        text: "Keypad controls",
      },
      {
        type: "table",
        headers: ["Key", "Action"],
        rows: [
          ["0–9", "Append digit to entered code"],
          ["#", "Submit the code for validation"],
          ["*", "Clear the entered code and start over"],
        ],
      },
      {
        type: "heading",
        text: "TOTP timing",
      },
      {
        type: "list",
        items: [
          "TOTP codes rotate every 60 seconds",
          "The backend accepts codes from the current window plus one window on each side to tolerate clock drift",
          "If the code is rejected with 'Wrong TOTP code', wait for the next code cycle in the app",
          "If the code is rejected with 'No unlock earned', the student has no active eligibility — they need to solve a CTF challenge first",
        ],
      },
      {
        type: "callout",
        variant: "info",
        text: "The fridge OLED display shows user-friendly error messages. 'ID not found' means the Member ID was not recognised. 'Account inactive' means the student has been deactivated in the dashboard.",
      },
    ],
  },
  {
    id: "ctf-integration",
    title: "CTF Range Integration",
    description: "How challenge completions grant fridge credits and access",
    blocks: [
      {
        type: "paragraph",
        text: "FRZR BURN connects to the cyber range via a webhook. When a student captures a flag, the range sends a signed event to the backend, which grants an unlock eligibility window and awards credits.",
      },
      {
        type: "heading",
        text: "What happens when a flag is captured",
      },
      {
        type: "steps",
        items: [
          "Student solves a challenge on the cyber range",
          "The range sends a POST request to /events/flag-captured with the student's Member ID, challenge details, and point value",
          "The backend verifies the HMAC-SHA256 signature and finds the matching student",
          "A 1-hour unlock eligibility window is created for that student",
          "Credits are awarded: challenge points ÷ 10 = credits (e.g. a 50-point challenge = 5 credits)",
          "The student now has 1 hour to walk to the fridge and enter their code",
        ],
      },
      {
        type: "heading",
        text: "Webhook format",
      },
      {
        type: "code",
        label: "POST /events/flag-captured",
        lines: [
          '// Header',
          'X-Range-Signature: sha256=<hmac-sha256-hex>',
          '// or',
          'Authorization: Bearer <RANGE_WEBHOOK_SECRET>',
          '',
          '// Body',
          '{',
          '  "range_challenge_id": "web-01",',
          '  "title":             "SQL Injection 101",',
          '  "points":            50,',
          '  "student_member_id": "0636"',
          '}',
        ],
      },
      {
        type: "heading",
        text: "Demo Cyber Range",
      },
      {
        type: "paragraph",
        text: "A demo range site is included for testing at http://localhost:5050. It has 6 built-in challenges across Web, Crypto, Network, and Recon categories. Students register using the pre-filled link in their enrollment email.",
      },
      {
        type: "steps",
        items: [
          "Enroll a student via the dashboard",
          "Open the MailHog inbox at http://localhost:8025 (dev) or check the student's real inbox",
          "Click the 'Register on the Cyber Range' button in the email — Member ID is pre-filled",
          "Log in to the range → solve a challenge → submit the flag",
          "Return to the dashboard → Students → click the student → verify credits in the ledger",
        ],
      },
      {
        type: "heading",
        text: "Eligibility windows",
      },
      {
        type: "list",
        items: [
          "Each flag capture creates a separate 1-hour window",
          "Windows stack — solving three challenges before visiting the fridge gives three unlock attempts",
          "Each valid fridge unlock consumes exactly one window",
          "Deactivating a student immediately invalidates all their unconsumed windows",
          "Expired windows (older than 1 hour) are automatically ignored",
        ],
      },
    ],
  },
  {
    id: "email-setup",
    title: "Email Setup",
    description: "Configuring SMTP so enrollment emails are delivered",
    blocks: [
      {
        type: "paragraph",
        text: "FRZR BURN requires SMTP to send enrollment emails. Without SMTP configured, student accounts cannot be created. For local development, MailHog captures all outgoing emails so they never reach real inboxes.",
      },
      {
        type: "heading",
        text: "Local development (MailHog)",
      },
      {
        type: "paragraph",
        text: "MailHog runs automatically with docker compose up. View all captured emails at http://localhost:8025. No configuration is needed — it works out of the box.",
      },
      {
        type: "heading",
        text: "Production — Brevo (recommended, free)",
      },
      {
        type: "steps",
        items: [
          "Sign up at brevo.com (no credit card required — 300 emails/day free)",
          "Go to SMTP & API → SMTP tab → generate a new SMTP key",
          "Go to Senders & IPs → verify your sender email address",
          "Update .env with the values below",
          "Restart: docker compose down && docker compose up",
        ],
      },
      {
        type: "code",
        label: ".env — Brevo settings",
        lines: [
          "SMTP_HOST=smtp-relay.brevo.com",
          "SMTP_PORT=587",
          "SMTP_USERNAME=your-brevo-login@example.com",
          "SMTP_PASSWORD=your-brevo-smtp-key",
          "SMTP_STARTTLS=true",
          "SMTP_FROM=your-verified-sender@example.com",
          "SMTP_FROM_NAME=FRZR BURN",
        ],
      },
      {
        type: "heading",
        text: "Production — Gmail",
      },
      {
        type: "steps",
        items: [
          "Enable 2-Step Verification on your Google account",
          "Go to Google Account → Security → App Passwords → generate one for Mail",
          "Update .env with the values below",
        ],
      },
      {
        type: "code",
        label: ".env — Gmail settings",
        lines: [
          "SMTP_HOST=smtp.gmail.com",
          "SMTP_PORT=587",
          "SMTP_USERNAME=yourname@gmail.com",
          "SMTP_PASSWORD=xxxx xxxx xxxx xxxx",
          "SMTP_STARTTLS=true",
          "SMTP_FROM=yourname@gmail.com",
          "SMTP_FROM_NAME=FRZR BURN",
        ],
      },
      {
        type: "callout",
        variant: "info",
        text: "Gmail allows up to 500 emails/day. Brevo allows 300/day on the free plan. For a typical class of 30 students, either option is more than sufficient.",
      },
    ],
  },
  {
    id: "managing-students",
    title: "Managing Students",
    description: "Editing, deactivating, resetting TOTP, and deleting students",
    blocks: [
      {
        type: "paragraph",
        text: "The Students page lists all enrolled students with their status, Member ID, and credit balance. Click any student to open their detail page.",
      },
      {
        type: "heading",
        text: "Student detail page actions",
      },
      {
        type: "table",
        headers: ["Action", "What it does"],
        rows: [
          ["Edit", "Update the student's name or email address"],
          ["Reset TOTP", "Invalidates the current TOTP secret and shows a new QR code (shown once)"],
          ["Deactivate / Activate", "Toggles whether the student can use the fridge"],
          ["Delete", "Permanently removes the student and all associated data"],
        ],
      },
      {
        type: "heading",
        text: "Resetting TOTP",
      },
      {
        type: "steps",
        items: [
          "Open the student detail page",
          "Click Reset TOTP",
          "A new QR code and secret key appear — have the student add it to their authenticator app",
          "The old TOTP secret is invalidated immediately",
          "Remind the student to delete the old entry from their authenticator app",
        ],
      },
      {
        type: "callout",
        variant: "warning",
        text: "After a TOTP reset, the student must set the interval to 60 seconds (not the default 30) when adding the new key to their authenticator app.",
      },
      {
        type: "heading",
        text: "Deactivating a student",
      },
      {
        type: "paragraph",
        text: "Deactivation takes effect immediately. All unconsumed eligibility windows are invalidated — the student cannot unlock the fridge even with a valid TOTP code. Credits are preserved and the student can be reactivated at any time.",
      },
      {
        type: "heading",
        text: "Deleting a student",
      },
      {
        type: "paragraph",
        text: "Deletion is permanent and removes the student along with all their ledger entries and eligibility windows. A confirmation dialog is shown before the action is taken. This cannot be undone.",
      },
      {
        type: "callout",
        variant: "warning",
        text: "Deactivate a student first if you are unsure — it blocks fridge access while keeping all data intact. Only delete when you are certain the record is no longer needed.",
      },
      {
        type: "heading",
        text: "Pagination",
      },
      {
        type: "paragraph",
        text: "The student list loads 50 students at a time. If there are more, a Load more button appears at the bottom of the table.",
      },
    ],
  },
  {
    id: "devices",
    title: "Devices",
    description: "Monitoring fridge hardware status",
    blocks: [
      {
        type: "paragraph",
        text: "The Devices page shows all registered ESP32 fridge controllers, their current online status, firmware version, and when they were last seen.",
      },
      {
        type: "heading",
        text: "Online status",
      },
      {
        type: "table",
        headers: ["Status", "Meaning"],
        rows: [
          ["Online (green)", "Device sent a heartbeat within the last 60 seconds"],
          ["Offline (grey)", "No heartbeat received in the last 60 seconds"],
        ],
      },
      {
        type: "list",
        items: [
          "Devices send a heartbeat immediately after connecting to WiFi",
          "After that, heartbeats are sent every 5 minutes",
          "A heartbeat is also sent any time a code validation attempt is made",
          "If a device goes offline, it will appear offline within 60 seconds",
        ],
      },
      {
        type: "callout",
        variant: "info",
        text: "Forced-open events (door physically opened without a valid code) are logged in the Unlock Events audit log with result 'forced_open'. Check there if you suspect a device has been tampered with.",
      },
    ],
  },
  {
    id: "items-inventory",
    title: "Items & Inventory",
    description: "Managing what's in the fridge",
    blocks: [
      {
        type: "paragraph",
        text: "Items are the redeemable goods stored in the fridge. Each item has a name, a credit cost, and a stock quantity. Items with zero stock are automatically excluded from the redemption form.",
      },
      {
        type: "heading",
        text: "Adding an item",
      },
      {
        type: "steps",
        items: [
          "Navigate to Items in the sidebar",
          "Click Add Item",
          "Enter the item name (e.g. 'Gatorade', 'Red Bull', 'Granola Bar')",
          "Set the credit cost — how many credits a student must spend to redeem this item",
          "Set the initial stock quantity",
          "Click Create",
        ],
      },
      {
        type: "callout",
        variant: "tip",
        text: "Set credit costs to reflect the relative value of items. If a Red Bull costs more than a granola bar, give it a higher credit cost so students make deliberate choices.",
      },
    ],
  },
  {
    id: "redemptions",
    title: "Processing Redemptions",
    description: "Exchanging student credits for fridge items",
    blocks: [
      {
        type: "paragraph",
        text: "Redemptions are processed by an admin at the fridge. When a student wants to claim an item, an admin opens the dashboard and processes the transaction.",
      },
      {
        type: "heading",
        text: "Processing a redemption",
      },
      {
        type: "steps",
        items: [
          "Navigate to Items in the sidebar",
          "Click Process Redemption",
          "Select the student — their Member ID and current credit balance are shown",
          "Select the item — cost and remaining stock are shown",
          "If the student has insufficient credits, the Redeem button is disabled",
          "Click Redeem — stock decrements and the student's new balance is shown",
        ],
      },
      {
        type: "callout",
        variant: "warning",
        text: "Redemptions cannot be undone through the dashboard. If you process one by mistake, contact your system administrator to correct the ledger directly.",
      },
    ],
  },
  {
    id: "unlock-events",
    title: "Unlock Events & Audit Log",
    description: "Reading the access attempt history",
    blocks: [
      {
        type: "paragraph",
        text: "Every code entry at the fridge keypad is logged — successful or not. The Unlock Events page is the complete audit trail for all access attempts.",
      },
      {
        type: "heading",
        text: "Result codes",
      },
      {
        type: "table",
        headers: ["Result", "Meaning"],
        rows: [
          ["granted", "Code was valid, eligibility window consumed, door unlocked"],
          ["invalid_format", "Code was not exactly 10 digits"],
          ["unknown_member", "The first 4 digits did not match any enrolled Member ID"],
          ["invalid_totp", "Member ID found but the 6-digit TOTP was wrong or expired"],
          ["no_eligibility", "Member ID and TOTP correct but no active eligibility window — student hasn't solved a challenge recently"],
          ["member_inactive", "The student account has been deactivated"],
          ["forced_open", "Door was physically opened while locked — no code was entered"],
        ],
      },
      {
        type: "callout",
        variant: "tip",
        text: "The 'no_eligibility' result is the most common failure during a CTF event. If many students see it, check that the cyber range webhook is correctly configured and sending events to the backend.",
      },
      {
        type: "heading",
        text: "Common issues",
      },
      {
        type: "table",
        headers: ["Symptom", "Likely cause"],
        rows: [
          ["invalid_totp repeatedly", "Student's authenticator is set to 30s interval instead of 60s"],
          ["no_eligibility after solving", "Webhook RANGE_WEBHOOK_SECRET mismatch — check both sides match"],
          ["unknown_member", "Student typed their Member ID wrong — verify it on their detail page"],
        ],
      },
    ],
  },
  {
    id: "troubleshooting",
    title: "Troubleshooting",
    description: "Common problems and how to fix them",
    blocks: [
      {
        type: "heading",
        text: "Bulk import — all rows skipped",
      },
      {
        type: "paragraph",
        text: "SMTP is not configured. Set SMTP_HOST in .env and restart. Accounts are only created when the enrollment email can be delivered.",
      },
      {
        type: "heading",
        text: "Webhook returns 401 Unauthorized",
      },
      {
        type: "paragraph",
        text: "The RANGE_WEBHOOK_SECRET in .env does not match what the cyber range is using. Both must be identical. After changing, restart both services.",
      },
      {
        type: "heading",
        text: "Webhook returns 404 — Student not found",
      },
      {
        type: "paragraph",
        text: "The student_member_id in the webhook payload does not match any student in the database. Verify the exact 4-digit Member ID in the student's detail page.",
      },
      {
        type: "heading",
        text: "TOTP codes rejected at the fridge",
      },
      {
        type: "list",
        items: [
          "Student set up their authenticator with 30-second interval — they must re-add the key with 60-second interval",
          "If TOTP_INTERVAL was recently changed on the server, reset the student's TOTP so they get a new secret provisioned at the correct interval",
          "Ensure the fridge firmware also uses a 60-second interval",
        ],
      },
      {
        type: "heading",
        text: "No space left on device (Docker)",
      },
      {
        type: "code",
        label: "Free up Docker disk space",
        lines: [
          "docker system prune -a --volumes",
          "docker compose up",
        ],
      },
      {
        type: "heading",
        text: "API container exits on startup",
      },
      {
        type: "paragraph",
        text: "Usually a missing required environment variable. Check that CLERK_SECRET_KEY, TOTP_ENCRYPTION_KEY, and RANGE_WEBHOOK_SECRET are all set in .env.",
      },
      {
        type: "callout",
        variant: "tip",
        text: "Run 'docker compose logs api' to see the exact error message from the API container.",
      },
    ],
  },
]
