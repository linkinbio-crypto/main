import aiosqlite
import uuid
import hashlib
from datetime import datetime, timezone

DB_PATH = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                key_id       TEXT PRIMARY KEY,
                created_by   TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                expires_at   TEXT,
                duration_days INTEGER,
                is_lifetime  INTEGER NOT NULL DEFAULT 0,
                is_redeemed  INTEGER NOT NULL DEFAULT 0,
                redeemed_by  TEXT,
                redeemed_at  TEXT,
                hwid         TEXT,
                is_blacklisted INTEGER NOT NULL DEFAULT 0,
                note         TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id   TEXT PRIMARY KEY,
                key_id       TEXT,
                hwid         TEXT,
                whitelisted  INTEGER NOT NULL DEFAULT 0,
                blacklisted  INTEGER NOT NULL DEFAULT 0,
                joined_at    TEXT NOT NULL,
                FOREIGN KEY (key_id) REFERENCES keys(key_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS hwid_resets (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id   TEXT NOT NULL,
                reset_by     TEXT NOT NULL,
                reset_at     TEXT NOT NULL,
                old_hwid     TEXT,
                reason       TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                action       TEXT NOT NULL,
                actor        TEXT NOT NULL,
                target       TEXT,
                detail       TEXT,
                timestamp    TEXT NOT NULL
            )
        """)
        await db.commit()


def generate_key() -> str:
    """Generate a UUID-based key in format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX (uppercase)."""
    return str(uuid.uuid4()).upper()


def hash_hwid(raw_hwid: str) -> str:
    """SHA-256 hash the HWID before storing."""
    return hashlib.sha256(raw_hwid.encode()).hexdigest()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Key operations ───────────────────────────────────────────────────────────

async def create_key(created_by: str, is_lifetime: bool, duration_days: int = None, note: str = None) -> str:
    key_id = generate_key()
    now = utcnow()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO keys (key_id, created_by, created_at, duration_days, is_lifetime, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key_id, created_by, now, duration_days, int(is_lifetime), note))
        await db.commit()
    return key_id


async def get_key(key_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM keys WHERE key_id = ?", (key_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def redeem_key(key_id: str, discord_id: str, hwid_raw: str) -> tuple[bool, str]:
    """
    Attempt to redeem a key for a user.
    Returns (success, message).
    """
    from datetime import timedelta

    key = await get_key(key_id)
    if not key:
        return False, "❌ Key not found."
    if key["is_blacklisted"]:
        return False, "❌ This key has been blacklisted."
    if key["is_redeemed"]:
        return False, "❌ This key has already been redeemed."

    # Check if user already has a key
    user = await get_user(discord_id)
    if user and user["key_id"]:
        return False, "❌ You already have an active key bound to your account."

    now = datetime.now(timezone.utc)
    expires_at = None
    if not key["is_lifetime"] and key["duration_days"]:
        expires_at = (now + timedelta(days=key["duration_days"])).isoformat()

    hwid_hash = hash_hwid(hwid_raw)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE keys SET is_redeemed=1, redeemed_by=?, redeemed_at=?, hwid=?, expires_at=?
            WHERE key_id=?
        """, (discord_id, utcnow(), hwid_hash, expires_at, key_id))

        if user:
            await db.execute("""
                UPDATE users SET key_id=?, hwid=? WHERE discord_id=?
            """, (key_id, hwid_hash, discord_id))
        else:
            await db.execute("""
                INSERT INTO users (discord_id, key_id, hwid, joined_at)
                VALUES (?, ?, ?, ?)
            """, (discord_id, key_id, hwid_hash, utcnow()))

        await db.commit()

    return True, "✅ Key redeemed successfully."


async def is_key_valid(key_id: str, discord_id: str, hwid_raw: str) -> tuple[bool, str]:
    """Validate key for an authenticated request (from external app)."""
    key = await get_key(key_id)
    if not key:
        return False, "Key not found."
    if key["is_blacklisted"]:
        return False, "Key is blacklisted."
    if not key["is_redeemed"]:
        return False, "Key has not been redeemed."
    if key["redeemed_by"] != discord_id:
        return False, "Key not bound to this user."

    # HWID check
    hwid_hash = hash_hwid(hwid_raw)
    if key["hwid"] != hwid_hash:
        return False, "HWID mismatch."

    # Expiry check
    if not key["is_lifetime"] and key["expires_at"]:
        expires = datetime.fromisoformat(key["expires_at"])
        if datetime.now(timezone.utc) > expires:
            return False, "Key has expired."

    # User blacklist check
    user = await get_user(discord_id)
    if user and user["blacklisted"]:
        return False, "User is blacklisted."

    return True, "Valid."


# ─── User operations ──────────────────────────────────────────────────────────

async def get_user(discord_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_whitelist(discord_id: str, state: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (discord_id, whitelisted, blacklisted, joined_at)
            VALUES (?, ?, 0, ?)
            ON CONFLICT(discord_id) DO UPDATE SET whitelisted=excluded.whitelisted
        """, (discord_id, int(state), utcnow()))
        await db.commit()


async def set_blacklist(discord_id: str, state: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (discord_id, whitelisted, blacklisted, joined_at)
            VALUES (?, 0, ?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET blacklisted=excluded.blacklisted
        """, (discord_id, int(state), utcnow()))
        await db.commit()


async def blacklist_key(key_id: str, state: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE keys SET is_blacklisted=? WHERE key_id=?", (int(state), key_id))
        await db.commit()


# ─── HWID operations ──────────────────────────────────────────────────────────

async def reset_hwid(discord_id: str, reset_by: str, reason: str = None) -> tuple[bool, str]:
    user = await get_user(discord_id)
    if not user or not user["key_id"]:
        return False, "User has no active key."

    old_hwid = user["hwid"]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET hwid=NULL WHERE discord_id=?", (discord_id,))
        await db.execute("UPDATE keys SET hwid=NULL WHERE key_id=?", (user["key_id"],))
        await db.execute("""
            INSERT INTO hwid_resets (discord_id, reset_by, reset_at, old_hwid, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (discord_id, reset_by, utcnow(), old_hwid, reason))
        await db.commit()

    return True, "✅ HWID reset successfully. The user must re-bind on next launch."


async def bind_hwid(discord_id: str, hwid_raw: str) -> tuple[bool, str]:
    user = await get_user(discord_id)
    if not user or not user["key_id"]:
        return False, "No active key found for this user."
    if user["hwid"]:
        return False, "HWID already bound. Use `/hwidreset` to clear it first."

    hwid_hash = hash_hwid(hwid_raw)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET hwid=? WHERE discord_id=?", (hwid_hash, discord_id))
        await db.execute("UPDATE keys SET hwid=? WHERE key_id=?", (hwid_hash, user["key_id"]))
        await db.commit()

    return True, "✅ HWID bound successfully."


# ─── Audit log ────────────────────────────────────────────────────────────────

async def log_action(action: str, actor: str, target: str = None, detail: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO audit_log (action, actor, target, detail, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (action, actor, target, detail, utcnow()))
        await db.commit()


async def get_audit_log(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
