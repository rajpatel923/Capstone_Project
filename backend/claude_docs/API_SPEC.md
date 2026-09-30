# API specification

Base URL: `/api/v1`. All request/response bodies are JSON. All timestamps are ISO 8601 UTC.

## Conventions

- **Auth headers:** admin endpoints require `Authorization: Bearer <clerk-session-jwt>` —
  this backend does not issue its own tokens; it verifies the JWT Clerk already issued to
  the frontend (see `## Auth`, below, and ADR-007). Device endpoints require
  `X-Device-Key: <raw key>`. The webhook endpoint requires `X-Range-Signature: <hmac>`.
- **Error shape** (all 4xx/5xx except Pydantic validation errors, which use FastAPI's default
  422 shape):
  ```json
  { "error": { "code": "string_identifier", "message": "human-readable", "details": {} } }
  ```
- **Business declines are not HTTP errors.** An invalid unlock code is a normal, expected
  outcome of calling `validate-code` — it returns `200` with `"valid": false`, not a 4xx.
  Reserve 4xx for malformed requests, bad auth, and missing resources.
- **Pagination:** list endpoints accept `?limit=` (default 25, max 100) and `?cursor=`,
  return `{ "items": [...], "next_cursor": "string | null" }`.

---

## Auth

There is no `/auth/login` endpoint in this backend — Clerk owns instructor/admin login
entirely. The frontend integrates Clerk's SDK (hosted sign-in UI or embedded components),
and once a session exists, Clerk gives the frontend a session JWT automatically. The
frontend attaches it as `Authorization: Bearer <token>` on every request to this API.

The backend's only job is **verification, not issuance**: on startup, fetch and cache
Clerk's JWKS (JSON Web Key Set) for this Clerk instance, and on every admin-protected
request, verify the JWT's signature against it and check `exp`/`nbf` as normal. Use Clerk's
official Python backend SDK if it fits the framework cleanly; a manual PyJWT + JWKS
verification is an acceptable fallback and is what the reference implementation below
assumes.

```python
# app/core/security.py — sketch, not exhaustive
from fastapi import Depends, HTTPException, Header
import jwt
from jwt import PyJWKClient

jwk_client = PyJWKClient("https://<your-clerk-domain>/.well-known/jwks.json")

def require_admin(authorization: str = Header(...)) -> dict:
    token = authorization.removeprefix("Bearer ").strip()
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(token, signing_key.key, algorithms=["RS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, {"error": {"code": "invalid_token", "message": "..."}})
    return claims  # claims["sub"] is the Clerk user id — use it for audit fields, see DATA_MODEL.md
```

**Do not** build a parallel password-based login path "just in case" — Clerk is the only
admin identity source. If a request needs to record *which* admin performed an action
(creating an item, resetting a student's TOTP secret), use `claims["sub"]` (the Clerk user
id) as that reference, not a locally-issued user id.

---

## Students

### `POST /students`

Enroll a new student. Generates a TOTP secret and returns its provisioning URI **once** —
the raw secret is never retrievable again after this call. If the instructor loses it, the
only recovery path is `POST /students/{id}/reset-totp`, which invalidates the old secret.

**Auth:** Clerk session JWT (see `## Auth` above)

**Request:**
```json
{ "member_id": "1042", "full_name": "Jordan Lee", "email": "jlee@islander.tamucc.edu" }
```
`member_id` is a 4-digit string, unique, chosen by the instructor (not auto-generated) so
it can match an existing ICS membership number if one already exists.

**Response `201`:**
```json
{
  "id": "uuid",
  "member_id": "1042",
  "full_name": "Jordan Lee",
  "email": "jlee@islander.tamucc.edu",
  "active": true,
  "totp_provisioning_uri": "otpauth://totp/FRZRBURN:1042?secret=...&issuer=FRZRBURN",
  "created_at": "2026-09-30T12:00:00Z"
}
```
The frontend should render `totp_provisioning_uri` as a QR code immediately and never log
or persist it client-side beyond that render.

**Response `409`:** `{ "error": { "code": "member_id_taken", "message": "..." } }`

### `GET /students`

**Auth:** Clerk session JWT · **Query:** `?limit=&cursor=&active=true|false`

**Response `200`:**
```json
{
  "items": [
    { "id": "uuid", "member_id": "1042", "full_name": "Jordan Lee", "active": true,
      "credit_balance": 40, "pending_eligibility_count": 1 }
  ],
  "next_cursor": null
}
```

### `GET /students/{id}`

Full detail including recent unlock events (last 10, inline) and ledger summary.

### `PATCH /students/{id}`

**Request (any subset):** `{ "full_name": "string", "active": false }`
Deactivating a student immediately invalidates all their unconsumed eligibilities.

### `POST /students/{id}/reset-totp`

Invalidates the current secret, generates a new one, returns a new `totp_provisioning_uri`
(same one-time-visibility rule as enrollment). Use when a student loses their authenticator.

---

## CTF range integration

### `POST /events/flag-captured`

Webhook called by the CTF range when a student solves a challenge. **The exact payload
shape below is a placeholder** pending confirmation of the range's actual webhook contract
— do not build against this without confirming it first (see `DECISIONS.md`).

**Auth:** `X-Range-Signature` header — HMAC-SHA256 of the raw request body, using
`RANGE_WEBHOOK_SECRET`. Requests with a missing or invalid signature return `401` and are
not processed or logged beyond a security-audit log entry.

**Request (assumed shape):**
```json
{
  "member_id": "1042",
  "challenge_id": "web-101",
  "challenge_title": "Basic SQLi",
  "points": 50,
  "solved_at": "2026-09-30T14:22:00Z"
}
```

**Response `200`:**
```json
{ "eligibility_granted": true, "eligibility_id": "uuid", "expires_at": "2026-09-30T15:22:00Z" }
```
Eligibility defaults to a 1-hour window (configurable). Credits are awarded in the same
transaction: `credit_delta = points // 10` (configurable policy, not hardcoded — see
`DATA_MODEL.md`).

**Response `404`:** unknown `member_id` — `{ "error": { "code": "unknown_member", ... } }`.
Log this loudly; it usually means the range and the roster are out of sync.

---

## Device

All device endpoints require `X-Device-Key`, a per-device key issued when the device is
registered (`POST /devices` — admin-only, not detailed here as it's a one-time setup call).

### `POST /devices/{device_id}/validate-code`

The security-critical endpoint. Called by the device when a student finishes keypad entry.

**Request:**
```json
{ "code": "10428675" }
```
`code` is the concatenation of 4-digit `member_id` + 6-digit TOTP, no separator, exactly 10
digits. Reject anything else at the schema level (422) before it reaches business logic.

**Response `200` (granted):**
```json
{ "valid": true, "member_id": "1042", "credit_balance": 35 }
```

**Response `200` (declined) — `reason` is one of `invalid_format | unknown_member |
invalid_totp | no_eligibility | member_inactive`:**
```json
{ "valid": false, "reason": "no_eligibility" }
```

**Response `429`:** rate limit exceeded for this device —
`{ "error": { "code": "rate_limited", "message": "...", "details": { "retry_after_seconds": 42 } } }`

Implementation notes for whoever builds this:
- Split the 10-digit code into `member_id = code[:4]`, `totp_input = code[4:]` before any
  lookup.
- Verify TOTP with a ±1 time-step window (30s each side) to tolerate clock drift — not
  wider than that.
- Use a constant-time comparison for the TOTP check (`pyotp.TOTP.verify` already does this
  correctly — don't reimplement it with `==`).
- Check eligibility and rate limit *before* revealing whether the member_id itself was
  valid, so the error reasons above don't become a member_id enumeration oracle in practice
  — rate limiting covers this in v1; don't skip it because "reason" already looks granular.

### `POST /devices/{device_id}/events`

Device-reported state events — forced-open, heartbeat.

**Request:** `{ "event_type": "forced_open" | "heartbeat" | "armed", "occurred_at": "iso8601" }`

**Response `202`:** `{}` — fire-and-forget from the device's perspective, no meaningful
response body needed.

### `GET /devices/{device_id}/state`

Polled by the device (and reusable by the dashboard) to check for a pending remote command.
v1 always returns `pending_command: null` — this endpoint exists so the contract is stable
when remote-unlock-override is built later, without a breaking API change.

**Response `200`:** `{ "pending_command": null }`

---

## Dashboard

All endpoints in this section require a Clerk session JWT (see `## Auth` above).

### `GET /dashboard/unlock-events`

**Query:** `?limit=&cursor=&student_id=&result=&from=&to=`

**Response `200`:**
```json
{
  "items": [
    { "id": "uuid", "student_id": "uuid", "member_id": "1042", "device_id": "fridge-01",
      "result": "granted", "created_at": "2026-09-30T15:01:00Z" }
  ],
  "next_cursor": null
}
```

### `GET /students/{id}/ledger`

**Response `200`:**
```json
{
  "items": [
    { "id": "uuid", "delta": 5, "reason": "challenge:web-101", "created_at": "..." },
    { "id": "uuid", "delta": -3, "reason": "redemption:item-soda", "created_at": "..." }
  ],
  "balance": 35
}
```

### `GET /devices`

**Response `200`:** list of registered devices with `last_seen_at`, `firmware_version`,
and a derived `status: "online" | "stale" | "unknown"` (stale = no heartbeat in 5 minutes).

---

## Items and redemption

### `GET /items`

**Response `200`:** `{ "items": [ { "id": "uuid", "name": "Gatorade", "cost_credits": 8, "stock_qty": 12 } ] }`

### `POST /items`

**Auth:** Clerk session JWT · **Request:** `{ "name": "string", "cost_credits": 8, "stock_qty": 12 }`

### `POST /redemptions`

Admin- or kiosk-triggered (not student-self-service in v1 — there is no student-facing app).

**Request:** `{ "member_id": "1042", "item_id": "uuid" }`

**Response `201`:** `{ "id": "uuid", "credit_balance_after": 27 }`

**Response `409`:** insufficient credits or zero stock —
`{ "error": { "code": "insufficient_credits" | "out_of_stock", ... } }`

---

## v2 (deferred — do not implement yet)

### `WS /ws/dashboard`

Auth via the Clerk session JWT passed as a query param at connection time (`?token=`),
verified the same way as REST requests (JWKS check), since WebSocket handshakes can't carry
custom headers from a browser `WebSocket` client. Server pushes:
```json
{ "type": "unlock_event", "payload": { "...same shape as GET /dashboard/unlock-events item..." } }
{ "type": "device_status", "payload": { "device_id": "fridge-01", "status": "online" } }
```
No client-to-server messages expected beyond the initial connection. Do not build this
until v1 polling is working and demonstrated — see `DECISIONS.md`.
