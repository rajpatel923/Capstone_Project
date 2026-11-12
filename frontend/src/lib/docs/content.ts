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
        text: "FRZR BURN is a CTF-gated smart mini-fridge reward system for the Islander Cyber Society. Students earn physical access to the fridge — and credits redeemable for items inside it — by solving cybersecurity challenges on the CTF range.",
      },
      {
        type: "heading",
        text: "The three-layer system",
      },
      {
        type: "list",
        items: [
          "CTF Range — students solve challenges, the range fires a webhook to the backend",
          "Backend API — validates codes, manages eligibility windows, tracks credits",
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
          "Enroll students and provision their TOTP authenticator",
          "Monitor device heartbeat and firmware versions",
          "Review every unlock attempt in the audit log",
          "Manage fridge inventory and process credit redemptions",
          "Deactivate or reset credentials for any student",
        ],
      },
      {
        type: "callout",
        variant: "info",
        text: "Students never log in to this dashboard. Their only interaction with the system is at the fridge keypad and in their authenticator app.",
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
        text: "Dashboard overview",
      },
      {
        type: "paragraph",
        text: "The Overview page shows four key metrics at a glance:",
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
        type: "paragraph",
        text: "Below the stats, the most recent unlock attempts are listed. Use the left sidebar to navigate to full management pages for Students, Devices, Events, and Items.",
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
    description: "Adding a new student and setting up their TOTP",
    blocks: [
      {
        type: "paragraph",
        text: "Each student needs a unique 4-digit member ID and a TOTP secret provisioned to their authenticator app. This is a one-time setup — the TOTP secret is shown only once at enrollment.",
      },
      {
        type: "heading",
        text: "Step-by-step enrollment",
      },
      {
        type: "steps",
        items: [
          "Navigate to Students in the sidebar",
          "Click New Student in the top-right",
          "Enter the student's 4-digit Member ID (use their ICS membership number if one exists — it must be unique across all students)",
          "Enter their Full Name and Email address",
          "Click Enroll — the form submits and a QR code appears",
          "Have the student immediately scan the QR code with Google Authenticator, Authy, or any TOTP app",
          "Click Done — the QR code cannot be retrieved again after this dialog closes",
        ],
      },
      {
        type: "callout",
        variant: "warning",
        text: "The TOTP provisioning QR code is shown exactly once. If the student misses it, you must reset their TOTP secret via the student detail page, which generates a new QR code.",
      },
      {
        type: "heading",
        text: "Member ID rules",
      },
      {
        type: "list",
        items: [
          "Must be exactly 4 digits (0000–9999)",
          "Must be unique — the system rejects duplicates",
          "Cannot be changed after enrollment (it is baked into the student's keypad code)",
          "If the student has an existing ICS membership number, use that for consistency",
        ],
      },
    ],
  },
  {
    id: "totp-codes",
    title: "TOTP Codes & the Keypad",
    description: "How students unlock the fridge",
    blocks: [
      {
        type: "paragraph",
        text: "The fridge keypad accepts a 10-digit code: the student's 4-digit member ID followed immediately by their current 6-digit TOTP code from their authenticator app. No spaces or separators.",
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
          "TOTP codes rotate every 30 seconds (standard RFC 6238)",
          "The backend accepts codes from the current window plus one window on each side (±30s) to tolerate clock drift",
          "If the code is rejected with 'Wrong TOTP code', the student should wait for the next code cycle in their app",
          "If the code is rejected with 'No unlock earned', the student has no active eligibility — they need to solve a CTF challenge first",
        ],
      },
      {
        type: "callout",
        variant: "info",
        text: "The fridge OLED display shows user-friendly error messages. 'ID not found' means the member ID was not recognised. 'Account inactive' means the student has been deactivated in the dashboard.",
      },
    ],
  },
  {
    id: "ctf-integration",
    title: "CTF Integration",
    description: "How challenge completions grant fridge access",
    blocks: [
      {
        type: "paragraph",
        text: "FRZR BURN connects to an external CTF range via a webhook. When a student captures a flag, the range sends a signed event to the backend, which grants an unlock eligibility window and awards credits.",
      },
      {
        type: "heading",
        text: "What happens when a flag is captured",
      },
      {
        type: "steps",
        items: [
          "Student solves a challenge on the CTF range",
          "The range sends a POST request to /events/flag-captured with the student's member ID, challenge details, and point value",
          "The backend verifies the HMAC-SHA256 signature and finds the matching student",
          "A 1-hour unlock eligibility window is created for that student",
          "Credits are awarded: challenge points ÷ 10 = credits (e.g. a 50-point challenge = 5 credits)",
          "The student now has 1 hour to walk to the fridge and enter their code",
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
      {
        type: "callout",
        variant: "tip",
        text: "Credits are awarded per flag capture regardless of whether the student visits the fridge. A student who solves challenges but never unlocks the fridge still accumulates credits that can be redeemed later.",
      },
      {
        type: "heading",
        text: "Credit conversion rate",
      },
      {
        type: "paragraph",
        text: "The default rate is 10 points per credit (configurable via the CREDIT_CONVERSION_RATE environment variable on the backend). A 100-point challenge awards 10 credits. Zero-point challenges award no credits but still grant an eligibility window.",
      },
    ],
  },
  {
    id: "managing-students",
    title: "Managing Students",
    description: "Editing, deactivating, and resetting TOTP",
    blocks: [
      {
        type: "paragraph",
        text: "The Students page lists all enrolled students with their status and enrollment date. Click any row to open the student detail page.",
      },
      {
        type: "heading",
        text: "Student detail page",
      },
      {
        type: "list",
        items: [
          "Member ID and current credit balance shown at the top",
          "Credit Ledger tab shows every credit transaction (challenges earned, redemptions spent)",
          "Edit button: update the student's name or email",
          "Reset TOTP button: invalidates the current TOTP secret and generates a new QR code (shown once)",
          "Deactivate / Activate toggle: controls whether the student can use the fridge",
        ],
      },
      {
        type: "heading",
        text: "Deactivating a student",
      },
      {
        type: "paragraph",
        text: "Deactivating a student via PATCH /students/{id} with active: false immediately invalidates all their unconsumed eligibility windows. They can no longer unlock the fridge even with a valid TOTP code. Credits are preserved and the student can be reactivated at any time.",
      },
      {
        type: "callout",
        variant: "warning",
        text: "Deactivation takes effect immediately. If a student is currently at the fridge when you deactivate them, their next code entry will be rejected with 'Account inactive'.",
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
          "A new QR code appears — have the student scan it immediately",
          "The old TOTP secret is invalidated as soon as the new one is generated",
          "The student's member ID and credits are unchanged",
        ],
      },
      {
        type: "heading",
        text: "Pagination",
      },
      {
        type: "paragraph",
        text: "The student list loads 50 students at a time. If there are more, a Load more button appears at the bottom of the table. The count shown in the header may read '50+ enrolled' when additional pages exist.",
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
        type: "paragraph",
        text: "The device list auto-refreshes every 30 seconds. A '(last refresh failed)' warning appears in the subtitle if the backend is unreachable during a refresh.",
      },
      {
        type: "heading",
        text: "Heartbeat behaviour",
      },
      {
        type: "list",
        items: [
          "Devices send a heartbeat immediately after connecting to WiFi",
          "After that, heartbeats are sent every 5 minutes",
          "A heartbeat is also sent any time a code validation attempt is made",
          "If a device goes offline (power cut, WiFi drop), it will appear offline within 60 seconds",
          "When WiFi reconnects, the device sends an immediate heartbeat",
        ],
      },
      {
        type: "heading",
        text: "Firmware version",
      },
      {
        type: "paragraph",
        text: "The firmware version column shows the version string reported by the device at last contact. If a device shows a different version from others, it may need to be reflashed. Firmware updates currently require physical access to the device.",
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
          "Set the initial stock quantity — how many units are currently in the fridge",
          "Click Create",
        ],
      },
      {
        type: "heading",
        text: "Stock management",
      },
      {
        type: "list",
        items: [
          "Stock decrements automatically when a redemption is processed",
          "Items with 0 stock are hidden from the redemption form",
          "To restock an item, you currently need to delete and recreate it (or update stock via the backend directly — a UI for editing stock is a planned improvement)",
          "Physical fridge refills should be reflected in the system to keep counts accurate",
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
        text: "Redemptions are processed by an admin at the fridge — there is no self-service redemption for students in v1. When a student wants to claim an item, an admin opens the dashboard and processes the transaction.",
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
          "Select the student from the dropdown — their member ID and current credit balance are shown",
          "Select the item — cost and remaining stock are shown",
          "If the student has insufficient credits, the form shows a warning and the Redeem button is disabled",
          "Click Redeem — the transaction is recorded, stock decrements, and the success toast shows the student's new balance",
        ],
      },
      {
        type: "heading",
        text: "Credit ledger",
      },
      {
        type: "paragraph",
        text: "Every redemption is recorded in the student's credit ledger with reason 'redemption'. You can view the full transaction history on the student detail page. The ledger shows both positive entries (flag captures) and negative entries (redemptions).",
      },
      {
        type: "callout",
        variant: "warning",
        text: "Redemptions cannot be undone through the dashboard. If you process a redemption by mistake, you will need to manually add a correction entry via the backend API or database.",
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
          ["invalid_format", "Code was not exactly 10 digits — student entered too few or too many"],
          ["unknown_member", "The first 4 digits did not match any enrolled member ID"],
          ["invalid_totp", "Member ID was found but the 6-digit TOTP was wrong or expired"],
          ["no_eligibility", "Member ID and TOTP were correct but no active eligibility window exists (student hasn't solved a challenge recently)"],
          ["member_inactive", "The student account has been deactivated"],
          ["forced_open", "The door was physically opened while locked — no code was entered"],
        ],
      },
      {
        type: "heading",
        text: "Filtering events",
      },
      {
        type: "list",
        items: [
          "Use the result filter dropdown to show only a specific outcome",
          "Filter by 'forced_open' to check for tampering attempts",
          "Filter by 'no_eligibility' to identify students who are trying but haven't captured any flags",
          "Filter by 'granted' to see successful unlocks",
          "Click Load more at the bottom to fetch older events",
        ],
      },
      {
        type: "callout",
        variant: "tip",
        text: "The 'no_eligibility' result is the most common failure mode during a CTF event. If many students are seeing it, check whether the CTF range webhook is configured correctly and sending events to the backend.",
      },
      {
        type: "heading",
        text: "Member ID shown",
      },
      {
        type: "paragraph",
        text: "The 'Member ID' column in the event log shows the raw first 4 digits of the submitted code, even for failed attempts. This helps identify typos (e.g. a student entering 5 digits for their member ID instead of 4).",
      },
    ],
  },
]
