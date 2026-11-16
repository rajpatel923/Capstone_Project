import hashlib
import hmac as hmac_lib
import json
import os
import sqlite3
from datetime import datetime
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import (
    Flask, flash, g, redirect, render_template,
    request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

FRZR_API = os.getenv("FRZR_BURN_API_URL", "http://localhost:8000")
WEBHOOK_SECRET = os.getenv("RANGE_WEBHOOK_SECRET", "changeme")
DB_PATH = os.getenv("DATABASE", "range.db")

CHALLENGES = [
    {
        "id": "recon-01",
        "category": "Recon",
        "title": "Hello Ranger",
        "description": "Every journey starts somewhere. Submit this flag to earn your first credits.",
        "points": 10,
        "flag": "CTF{w3lc0m3_t0_th3_r4ng3}",
        "hint": "CTF{w3lc0m3_t0_th3_r4ng3}",
    },
    {
        "id": "web-01",
        "category": "Web",
        "title": "Robots Exposed",
        "description": (
            "Websites often hide secrets in <code>/robots.txt</code>. "
            "A misconfigured server leaked its admin path there.<br><br>"
            "Flag: <code>CTF{r0b0ts_txt_s3cr3ts}</code>"
        ),
        "points": 20,
        "flag": "CTF{r0b0ts_txt_s3cr3ts}",
        "hint": "curl https://target.example/robots.txt",
    },
    {
        "id": "crypto-01",
        "category": "Crypto",
        "title": "Base64 Basics",
        "description": (
            "Decode this Base64 string to find the flag:<br>"
            "<code>Q1RGe2I0czM2NF9pczBfdXMzbGVzc19jcnlwdDB9</code>"
        ),
        "points": 20,
        "flag": "CTF{b4s364_is0_us3less_crypt0}",
        "hint": "Python: import base64; base64.b64decode('Q1RG...').decode()",
    },
    {
        "id": "crypto-02",
        "category": "Crypto",
        "title": "Caesar's Cipher",
        "description": (
            "Decrypt this ROT13 message:<br>"
            "<code>PGS{ebg13_vf_a0g_frpher}</code>"
        ),
        "points": 30,
        "flag": "CTF{rot13_is_n0t_secure}",
        "hint": "Every letter shifts by 13. Try rot13.com",
    },
    {
        "id": "net-01",
        "category": "Network",
        "title": "Open Ports",
        "description": (
            "An attacker scanned a server and found a service running on port 8888. "
            "The banner revealed the flag.<br><br>"
            "Flag: <code>CTF{nmap_f0und_th3_p0rt}</code>"
        ),
        "points": 40,
        "flag": "CTF{nmap_f0und_th3_p0rt}",
        "hint": "nmap -sV -p 8888 target",
    },
    {
        "id": "web-02",
        "category": "Web",
        "title": "SQL Injection 101",
        "description": (
            "A login form was vulnerable to SQL injection. "
            "Using <code>' OR '1'='1' --</code> as the password bypassed authentication entirely.<br><br>"
            "Flag: <code>CTF{sql_1nj3ct10n_byp4ss}</code>"
        ),
        "points": 50,
        "flag": "CTF{sql_1nj3ct10n_byp4ss}",
        "hint": "' OR '1'='1' --",
    },
]

CATEGORY_COLORS = {
    "Web": "#1f6feb",
    "Crypto": "#8957e5",
    "Network": "#da3633",
    "Recon": "#bf8700",
}


# ── Database ───────────────────────────────────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            member_id    TEXT NOT NULL,
            created_at   TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS solves (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            challenge_id TEXT NOT NULL,
            solved_at    TEXT NOT NULL,
            webhook_ok   INTEGER NOT NULL DEFAULT 0,
            UNIQUE(user_id, challenge_id)
        );
    """)
    db.commit()
    db.close()


# ── Auth helpers ───────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Webhook ────────────────────────────────────────────────────────────────────

def fire_webhook(challenge: dict, member_id: str) -> tuple[bool, str]:
    payload = {
        "range_challenge_id": challenge["id"],
        "title": challenge["title"],
        "points": challenge["points"],
        "student_member_id": member_id,
    }
    body = json.dumps(payload, separators=(",", ":")).encode()
    sig = "sha256=" + hmac_lib.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    try:
        resp = requests.post(
            f"{FRZR_API}/events/flag-captured",
            data=body,
            headers={"Content-Type": "application/json", "X-Range-Signature": sig},
            timeout=5,
        )
        if resp.status_code == 204:
            return True, "ok"
        return False, f"API returned {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.ConnectionError:
        return False, f"Could not reach FRZR BURN at {FRZR_API}"
    except Exception as exc:
        return False, str(exc)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        member_id = request.form["member_id"].strip()

        if not username or not password or not member_id:
            flash("All fields are required.", "error")
        elif len(member_id) != 4 or not member_id.isdigit():
            flash("Member ID must be exactly 4 digits.", "error")
        else:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO users (username, password_hash, member_id, created_at) VALUES (?,?,?,?)",
                    (username, generate_password_hash(password), member_id, datetime.utcnow().isoformat()),
                )
                db.commit()
                flash("Account created! Log in to start.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Username already taken.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["member_id"] = user["member_id"]
            return redirect(url_for("challenges"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/challenges")
@login_required
def challenges():
    db = get_db()
    rows = db.execute(
        "SELECT challenge_id, webhook_ok FROM solves WHERE user_id = ?",
        (session["user_id"],),
    ).fetchall()
    solved = {row["challenge_id"]: bool(row["webhook_ok"]) for row in rows}
    total_pts = sum(c["points"] for c in CHALLENGES if c["id"] in solved)
    total_credits = total_pts // 10
    return render_template(
        "challenges.html",
        challenges=CHALLENGES,
        solved=solved,
        category_colors=CATEGORY_COLORS,
        total_pts=total_pts,
        total_credits=total_credits,
    )


@app.route("/solve", methods=["POST"])
@login_required
def solve():
    challenge_id = request.form.get("challenge_id", "")
    submitted = request.form.get("flag", "").strip()

    challenge = next((c for c in CHALLENGES if c["id"] == challenge_id), None)
    if not challenge:
        flash("Challenge not found.", "error")
        return redirect(url_for("challenges"))

    db = get_db()
    if db.execute(
        "SELECT id FROM solves WHERE user_id = ? AND challenge_id = ?",
        (session["user_id"], challenge_id),
    ).fetchone():
        flash(f'"{challenge["title"]}" is already solved.', "info")
        return redirect(url_for("challenges"))

    if submitted != challenge["flag"]:
        flash(f'Wrong flag for "{challenge["title"]}". Try again.', "error")
        return redirect(url_for("challenges"))

    ok, detail = fire_webhook(challenge, session["member_id"])

    db.execute(
        "INSERT INTO solves (user_id, challenge_id, solved_at, webhook_ok) VALUES (?,?,?,?)",
        (session["user_id"], challenge_id, datetime.utcnow().isoformat(), int(ok)),
    )
    db.commit()

    credits = challenge["points"] // 10
    if ok:
        flash(
            f'Flag correct! +{credits} credit{"s" if credits != 1 else ""} sent to FRZR BURN '
            f'(member {session["member_id"]}).',
            "success",
        )
    else:
        flash(
            f'Flag correct, but FRZR BURN webhook failed: {detail}. '
            f'Check your Member ID and that the API is running.',
            "warning",
        )
    return redirect(url_for("challenges"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5050)
