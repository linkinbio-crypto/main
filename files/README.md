# 🔐 Discord Auth Bot

A full-featured Discord license key system with HWID binding, whitelist/blacklist, and an HTTP verification API.

---

## 📁 Project Structure

```
discord_bot/
├── bot.py              # Main bot entry point
├── api.py              # HTTP verification API (for your app)
├── database.py         # SQLite schema + all DB operations
├── utils.py            # Shared helpers (is_admin, embeds)
├── cogs/
│   ├── keys.py         # /genkey, /keyinfo, /blacklistkey
│   ├── users.py        # /redeem, /userinfo, /whitelist, /blacklist, /hwidreset, /hwidbind
│   └── admin.py        # /auditlog, /stats, /synccommands
├── requirements.txt
└── .env.example
```

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your values
```

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Your bot token from Discord Developer Portal |
| `OWNER_ID` | Your personal Discord user ID (right-click → Copy ID) |
| `ADMIN_ROLE_ID` | Role ID that can use admin commands |
| `API_SECRET` | Shared secret for the HTTP verification API |
| `API_PORT` | Port for the HTTP API (default: 8080) |

### 3. Run the bot
```bash
python bot.py
```

### 4. Sync slash commands
Once the bot is online, run `/synccommands` in Discord to register all slash commands globally.

### 5. (Optional) Run the verification API
```bash
python api.py
```

---

## 🔑 Slash Commands

### Admin Commands
> Requires admin role or bot owner

| Command | Description |
|---|---|
| `/genkey [duration] [amount] [note]` | Generate 1–10 keys. Omit `duration` for lifetime. |
| `/keyinfo <key>` | View full details of a key |
| `/blacklistkey <key> <state>` | Blacklist or un-blacklist a key |
| `/whitelist <user> <state>` | Whitelist or un-whitelist a user |
| `/blacklist <user> <state>` | Blacklist or un-blacklist a user |
| `/hwidreset <user> [reason]` | Reset a user's bound HWID |
| `/hwidbind <user> <hwid>` | Manually bind an HWID to a user |
| `/userinfo <user>` | View a user's key, HWID, and status |
| `/auditlog [limit]` | View the last N audit log entries |
| `/stats` | Database statistics overview |
| `/synccommands` | Sync slash commands (owner only) |

### User Commands

| Command | Description |
|---|---|
| `/redeem <key> <hwid>` | Redeem a license key and bind HWID |

---

## 🌐 Verification API

Your external app (loader, launcher, etc.) calls this to validate a user at runtime.

### `POST /verify`
**Headers:**
```
X-API-Secret: your_api_secret
Content-Type: application/json
```

**Body:**
```json
{
  "key": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
  "discord_id": "123456789012345678",
  "hwid": "raw-hwid-string-from-machine"
}
```

**Response:**
```json
{ "valid": true,  "reason": "Valid." }
{ "valid": false, "reason": "HWID mismatch." }
```

### `GET /health`
```json
{ "status": "ok" }
```

---

## 🗄️ Database Schema

| Table | Purpose |
|---|---|
| `keys` | All generated keys with status, HWID, expiry |
| `users` | Discord user records with whitelist/blacklist flags |
| `hwid_resets` | Full history of every HWID reset |
| `audit_log` | Every admin action with actor, target, timestamp |

---

## 🔒 Security Notes

- HWIDs are **SHA-256 hashed** before storage — raw values are never saved
- All admin commands are **ephemeral** (only visible to the requester)
- The verification API requires a **shared secret header**
- Every admin action is recorded in the **audit log**
